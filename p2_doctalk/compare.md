# P2 DocTalk — Vector Store Comparison

Same RAG pipeline (load PDF → chunk → embed with `text-embedding-3-small` → store → query → ask Claude) implemented on three vector stores. This document captures the side-by-side comparison.

## The three implementations

| File | Vector store | Mode |
|---|---|---|
| `doctalk.py` | Qdrant | In-memory (`:memory:`) |
| `doctalk_langchain.py` | Qdrant | In-memory via LangChain abstraction |
| `doctalk_pinecone.py` | Pinecone | Serverless (cloud) |

Chroma is covered in the curriculum via `embed_intro.py` and the Onemyle Chatbot's semantic cache.

## Test setup

- PDF: `Mavic Drone Manual.pdf`
- Question: *"How do I return the drone to home automatically?"*
- Embedding: OpenAI `text-embedding-3-small`, 1536 dims, cosine
- Chunking: `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)`
- LLM: `claude-sonnet-4-6`, `max_tokens=1024`

## Observations (to fill in after running)

| Dimension | Qdrant in-mem | Pinecone serverless |
|---|---|---|
| Lines of code | TBD | TBD |
| First-ingest latency (PDF → index queryable) | TBD | TBD |
| Query p50 latency (embed + query + LLM) | TBD | TBD |
| Query p50 latency (embed + query only, no LLM) | TBD | TBD |
| Setup friction (account/auth/install) | None — pip install only | API key signup + `pinecone>=5.0` |
| Index persistence between runs | None (`:memory:`) | Persistent (managed cloud) |
| Cost at this workload | $0 | $0 (free tier) |
| Recall / answer quality | TBD | TBD |
| API ergonomics — `create + upsert + query` | TBD | TBD |

## When I'd pick each (preliminary)

- **Qdrant in-memory** — local development, unit tests, demos. Zero ops, restart-resets-everything is a feature for testing.
- **Qdrant self-hosted** — production where I want self-host control, rich filtering, hybrid search, cost predictability. The "Postgres of vector stores" choice.
- **Pinecone serverless** — production where managed simplicity outweighs vendor lock-in. Enterprise SLAs, zero ops, "we don't run any infrastructure" stance.
- **Chroma** — embedded use cases. Semantic caches inside an application (like the Onemyle Chatbot), small-corpus tutorials, prototyping.

## Senior framing

*"I've shipped the same RAG pipeline on Chroma (embedded SQLite), Qdrant (open-source Rust, both in-memory and self-host), and Pinecone (managed serverless). The pipeline code is nearly identical — only the storage layer changes. The real decision is operational: do I want to run nothing (Chroma embedded / Pinecone serverless), run my own infrastructure (Qdrant self-host), or pay someone else to run it (Pinecone / Qdrant Cloud). At our typical scale of low-millions of vectors, the latency differences are dominated by the LLM call that follows retrieval, so the pick is more about ops model and vendor risk than performance."*

## What's NEW about Pinecone in this comparison

Concepts the Pinecone variant demonstrates that the Qdrant in-memory version doesn't:

- **Index lifecycle** — created once via `pc.create_index(...)`, persists across runs, idempotent re-creation guard
- **Serverless cloud spec** — `ServerlessSpec(cloud="aws", region="us-east-1")`
- **Namespaces** — virtual partitions inside an index; one per source PDF
- **Async ready check** — index creation is non-blocking, must poll `describe_index().status["ready"]`
- **Batch upsert** — Pinecone caps batches at ~100 records / 2MB; we chunk our records accordingly
- **Metadata-inline-vs-external decision** — we chose inline (chunk text in metadata) so query responses include text directly

## What surprised me (to fill in)

- TBD after running
