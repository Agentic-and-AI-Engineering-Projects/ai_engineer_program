"""
P2 DocTalk — Pinecone variant.

Same RAG pipeline as doctalk.py (load PDF → chunk → embed → store → query → ask Claude),
only the vector store layer is swapped from Qdrant in-memory to Pinecone serverless.

Why this file exists:
- Portfolio piece. Demonstrates fluency with all three vector stores in the AI engineer's
  toolkit: Chroma (embedded), Qdrant (self-host / Rust server), Pinecone (managed SaaS).
- The same RAG pipeline running on three backends makes the tradeoffs comparable side-by-side.
  See compare.md for the writeup.

Pinecone concepts demonstrated:
- Serverless index creation (vs. pod-based; serverless is the post-2024 default)
- Idempotent index creation (check exists, skip if so)
- Namespace partitioning (one namespace per source document)
- Upsert with vector + metadata in one call (chunk text lives inline in metadata)
- Query with metadata included so the LLM gets text back, not just IDs

Usage:
    # First time: ingest the PDF (creates index + uploads chunks)
    python doctalk_pinecone.py --ingest "Mavic Drone Manual.pdf"

    # Subsequent queries (index persists in Pinecone serverless)
    python doctalk_pinecone.py --query "How do I return the drone to home automatically?"

    # Default behavior (no flags): ingest then ask the demo question
    python doctalk_pinecone.py

Setup:
    pip install "pinecone>=5.0"
    echo "PINECONE_API_KEY=pcsk_..." >> .env
"""

import argparse
import os
import time
import uuid

import anthropic
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec


load_dotenv()


# Pinecone configuration
INDEX_NAME = "doctalk-pinecone"
DIMENSION = 1536                         # text-embedding-3-small is 1536-dim
METRIC = "cosine"
CLOUD = "aws"
REGION = "us-east-1"

# Embedding model — same as Qdrant variant for apples-to-apples comparison
EMBED_MODEL = "text-embedding-3-small"

# Demo defaults — match the Qdrant variant exactly so we can compare answers
DEFAULT_PDF = "Mavic Drone Manual.pdf"
DEFAULT_QUESTION = "How do I return the drone to home automatically?"


def get_pinecone_client() -> Pinecone:
    """Initialize the Pinecone client from environment."""
    # Pinecone API key is required — fail loud if missing rather than silently 401
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "PINECONE_API_KEY is not set. Add it to .env (get one at pinecone.io)."
        )
    return Pinecone(api_key=api_key)


def get_or_create_index(pc: Pinecone):
    """Return a handle to the index, creating it if it doesn't exist yet.

    Idempotent — safe to call on every run. This is the production pattern;
    treating the index as a "managed resource we own" rather than something
    we recreate every run.
    """
    # List existing indexes — Pinecone's list_indexes returns IndexModel objects
    existing_names = [idx.name for idx in pc.list_indexes()]

    if INDEX_NAME not in existing_names:
        print(f"[pinecone] index '{INDEX_NAME}' not found, creating (serverless, {CLOUD}/{REGION})...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(cloud=CLOUD, region=REGION),
        )
        # Index creation is async — wait until it's queryable before returning
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            print("[pinecone] waiting for index to become ready...")
            time.sleep(2)
        print(f"[pinecone] index '{INDEX_NAME}' ready.")
    else:
        print(f"[pinecone] using existing index '{INDEX_NAME}'.")

    return pc.Index(INDEX_NAME)


def build_index(index, pdf_path: str, namespace: str):
    """Load PDF, split into chunks, embed, and upsert into Pinecone under namespace.

    Each chunk becomes one record: (id, vector, metadata). The chunk text itself
    lives in metadata under key 'text' — so the query response gives us the text
    directly without a second fetch.

    Re-ingest safety: we wipe the namespace before upsert. Chunk IDs are random
    UUIDs (regenerated every run), and chunk boundaries shift when the source
    document changes, so a plain upsert would accumulate orphaned chunks across
    re-ingests. Wiping first guarantees the namespace reflects only the current
    document state.
    """
    # Step 0 — wipe any prior version of this document's chunks in this namespace
    try:
        index.delete(delete_all=True, namespace=namespace)
        print(f"[ingest] wiped existing namespace '{namespace}' before re-ingest")
    except Exception as e:
        # Namespace may not exist yet on first run — that's fine
        print(f"[ingest] namespace '{namespace}' not present yet (fresh ingest): {e.__class__.__name__}")

    # Step 1 — load PDF and split into overlapping chunks (same params as Qdrant variant)
    print(f"[ingest] loading {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    document = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(document)
    print(f"[ingest] split into {len(chunks)} chunks")

    # Step 2 — embed each chunk
    embeddings_client = OpenAIEmbeddings(
        model=EMBED_MODEL,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # embed_documents takes a list of strings, returns list of 1536-dim vectors
    chunk_texts = [chunk.page_content for chunk in chunks]
    chunk_vectors = embeddings_client.embed_documents(chunk_texts)
    print(f"[ingest] embedded {len(chunk_vectors)} chunks with {EMBED_MODEL}")

    # Step 3 — build (id, vector, metadata) tuples for Pinecone upsert
    records = []
    for chunk, vector in zip(chunks, chunk_vectors):
        # Unique ID per chunk — UUID4 is fine, Pinecone doesn't care as long as it's unique
        chunk_id = str(uuid.uuid4())
        # Metadata payload — chunk text + page number live inline so query returns them
        metadata = {
            "text": chunk.page_content,
            "page": chunk.metadata.get("page", -1),
            "source": chunk.metadata.get("source", pdf_path),
        }
        records.append({"id": chunk_id, "values": vector, "metadata": metadata})

    # Step 4 — upsert in batches (Pinecone caps each upsert call at ~100 records / 2MB)
    BATCH_SIZE = 100
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        index.upsert(vectors=batch, namespace=namespace)
        print(f"[ingest] upserted batch {i // BATCH_SIZE + 1} ({len(batch)} records) → namespace='{namespace}'")

    print(f"[ingest] complete — {len(records)} vectors in namespace '{namespace}'")


def retrieve(index, question: str, namespace: str, k: int = 3):
    """Embed the question and query Pinecone for the top-k most similar chunks.

    Returns the raw matches list; format_context turns them into a string.
    include_metadata=True is critical — without it Pinecone returns only IDs.
    """
    # Embed the question with the SAME model used at ingest time
    embeddings_client = OpenAIEmbeddings(
        model=EMBED_MODEL,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    query_vector = embeddings_client.embed_query(question)

    # Query — namespace scopes the search to this document's vectors only
    response = index.query(
        vector=query_vector,
        top_k=k,
        namespace=namespace,
        include_metadata=True,
    )
    return response.matches


def format_context(matches) -> str:
    """Turn Pinecone's match list into a prompt-ready context string."""
    context = ""
    for i, match in enumerate(matches):
        # match.score = cosine similarity, match.metadata['text'] = the chunk
        page = match.metadata.get("page", "?")
        text = match.metadata.get("text", "")
        context += f"[Page: {page}, score: {match.score:.4f}]\n"
        context += f"Result {i + 1}: {text[:200]}...\n\n"
    return context


def ask_claude(question: str, context: str) -> str:
    """Send context + question to Claude and return the answer."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are a helpful assistant. Answer the question using only the context "
            "provided. Always mention which page(s) your answer comes from."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }
        ],
    )
    return response.content[0].text


def parse_args():
    parser = argparse.ArgumentParser(description="DocTalk — Pinecone variant")
    parser.add_argument(
        "--ingest",
        metavar="PDF",
        help="Path to a PDF to ingest (chunks + embeds + upserts to Pinecone)",
    )
    parser.add_argument(
        "--query",
        metavar="QUESTION",
        help="Question to ask against the existing index",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Namespace to use (default: derived from PDF filename)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of chunks to retrieve (default: 3)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Connect to Pinecone and ensure the index exists
    pc = get_pinecone_client()
    index = get_or_create_index(pc)

    # If --ingest given, run ingestion; otherwise we assume index is already populated
    if args.ingest:
        pdf_path = args.ingest
        # Namespace defaults to PDF filename — keeps documents cleanly separated
        namespace = args.namespace or os.path.basename(pdf_path)
        build_index(index, pdf_path, namespace=namespace)

    # If --query given, run a query; otherwise demo with default question
    question = args.query or DEFAULT_QUESTION
    namespace = args.namespace or os.path.basename(args.ingest or DEFAULT_PDF)

    print(f"\n[query] '{question}' against namespace '{namespace}'")
    matches = retrieve(index, question, namespace=namespace, k=args.top_k)

    print("\n--- Retrieved Context ---")
    context = format_context(matches)
    print(context)

    print("--- Claude's Answer ---")
    answer = ask_claude(question, context)
    print(answer)


if __name__ == "__main__":
    main()
