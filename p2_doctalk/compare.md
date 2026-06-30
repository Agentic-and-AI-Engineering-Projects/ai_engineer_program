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

## Observations (first run captured 2026-06-29)

| Dimension | Qdrant in-mem | Pinecone serverless |
|---|---|---|
| Lines of code | ~70 | ~190 (extra: idempotent index create, batched upsert, namespace mgmt) |
| First-ingest setup | `:memory:` — instant | Account signup + API key + `pip install pinecone>=5.0` |
| Index creation latency | N/A (in-memory) | ~10–30 sec (async, must poll `status.ready`) |
| Ingest wall-clock (289 chunks, 22 MB Mavic manual) | n/a (separate run) | PDF load ~30–60 sec + embed ~10 sec + 3 batched upserts |
| Recall / answer quality | n/a | 3/3 retrieved chunks relevant; cosine 0.59–0.62; Claude answer fully grounded with page citations |
| Index persistence between runs | None | Persistent (managed cloud) — namespace survives, re-ingest wipes & rebuilds |
| Cost at this workload | $0 | $0 (free tier; ~$0.001 OpenAI embedding cost) |
| Console visibility | None | Pinecone web console shows: index spec (AWS us-east-1, Dense, 1536 dims, On-demand), namespace browse with inline metadata (text + page), per-call metrics |
| Failure modes observed | n/a | (a) OpenAI 429 `insufficient_quota` — billing issue (fixed by topping up $5). (b) NotFoundError on first namespace delete — handled gracefully (re-ingest safety pattern). |

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

## What surprised me (first run)

- **Cosine scores were modest (0.59–0.62) even on a clean RTH question.** `text-embedding-3-small` doesn't push scores to 0.9+ on procedural-manual content — the right framing is "relative rank, not absolute confidence." All three top-3 results were genuinely relevant despite the modest absolute numbers.
- **Async index creation requires a poll loop.** Pinecone returns from `create_index()` immediately, but the index isn't queryable until `describe_index().status.ready == True`. Add ~10–30 sec to first-run wall-clock for this. Idempotent re-runs skip it.
- **Re-ingest safety needs `index.delete(delete_all=True, namespace=...)` BEFORE upsert.** UUID4 chunk IDs + shifting chunk boundaries on doc updates means a plain upsert would accumulate orphans. The wipe-then-rebuild pattern is what production teams actually do.
- **Pinecone web console shows the namespace + browseable metadata immediately** — chunk text inline in the payload is right there in the Browse tab. Useful sanity-check that the ingest landed correctly.
- **OpenAI billing is a separate failure surface from Pinecone.** Got a 429 `insufficient_quota` mid-ingest; topping up $5 cleared it for thousands of future runs. Worth noting that production systems on multi-provider stacks need budget alerts per provider, not just per Pinecone.
