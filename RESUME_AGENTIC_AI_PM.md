# RAJESH RAMANI, PMP, CSM
**Senior Program Manager · Agentic AI / AI Engineering**
Fremont, CA, USA
rajesh_ramani@icloud.com · (408) 806-0359
[linkedin.com/in/rvrajesh123](https://linkedin.com/in/rvrajesh123/) · [github.com/rrvenkatrama](https://github.com/rrvenkatrama/)

---

## PROFILE SUMMARY

Senior Program Manager and hands-on Agentic AI Engineer with extensive experience leading large-scale infrastructure programs and an active portfolio of production agentic-AI systems. Currently serving as investor / Agentic AI Product Consultant at a hyperlocal creator/business marketplace startup, where I design and ship **MatchScout** — a gig-driven AI recommender with rigorous outcome-based A/B evaluation. Author of the open-source **HPRC Framework**, an AI-native server-side templating engine. Track record of driving cross-functional agile delivery on multi-million-dollar programs. Bridge between product, engineering, and AI — equally fluent reading a LangGraph state machine and running a sprint review.

---

## CERTIFICATIONS

- **Project Management Professional (PMI-PMP)** — Renewed 2025
- **Certified ScrumMaster (CSM)**
- **AWS Certified Solutions Architect — Associate**
- **KCNA** — Kubernetes and Cloud Native Associate
- **Google Cloud Certified — Cloud Digital Leader**

---

## EDUCATION

- M.S., Information Systems — California State University, Los Angeles
- B.S., Computer Science — National Institute of Technology, India

---

## AI ENGINEERING CENTERPIECES

### MatchScout — Onemyle Marketplace AI Recommender
*LangGraph · Claude · sentence-transformers · SQLite · Streamlit · LangSmith*
GitHub: [Onemyle-matchscout](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout)

- Gig-driven AI recommender for a two-sided creator-business marketplace. Led as investor / consultant Product/AI Lead.
- **Multi-stage pipeline:** rules-based hard filter → vector cosine ranking → LLM re-ranker over the top candidates.
- **Outcome-based A/B evaluation:** held out a no-LLM control arm to measure whether the LLM actually moves real downstream gig outcomes. Quality is judged on real gig success, not synthetic golden sets.
- **Versioned prompts benchmarked against real outcomes:** each prompt version is evaluated on the downstream success of the creators it recommended — making prompt iteration empirically A/B-testable.
- **Observability & cost tracking:** LangSmith traces per LLM call with one-click drill-down from the outcome dashboard; per-call USD cost tracking for cost-per-arm comparisons alongside quality.

### HPRC Framework — Open-Source AI-Native Templating Engine
*Python · Apache-2.0 · asyncio · Pydantic v2 · FastAPI · pytest*
GitHub: [github.com/HPRCFramework/hprc-framework](https://github.com/HPRCFramework/hprc-framework) · Web: [hprcframework.dev](https://hprcframework.dev)

- Designed and built **HPRC** — an open-source server-side templating engine where developers embed LLM prompts directly in HTML (SPREP templates) and the framework executes them during page rendering. Inverts the usual imperative "Python calls LLM, stitches output into template" pattern.
- **Declarative render pipeline:** auto-builds a prompt dependency graph from `<include>` references; executes independent prompts **concurrently via `asyncio` topological scheduling**; TTL caches results keyed on the fully-resolved prompt.
- **Provider-agnostic LLM abstraction** with **six interchangeable adapters** (OpenAI, Anthropic, Gemini, Ollama/LM-Studio, mock, multi-provider router) behind a single coroutine interface; SDKs lazily/optionally loaded.
- **External rules + tools seams** (no expression language in templates): per-prompt conditional execution and allowlisted tool invocation.
- Authored the **SPREP language specification** (mini-RFC) plus full architecture/user docs and a **66-test** suite including a mocked provider-conformance harness.

---

## PROFESSIONAL EXPERIENCE

### Investor / Agentic AI Product Consultant · Onemyle (Hyperlocal Creator/Business Marketplace Startup)
*Mar 2026 – Present · Remote*

- Angel investor and active product partner. Lead AI strategy, technical architecture, and product direction. Run sprint cadence and roadmap reviews.
- **Designing, shipping and developing MatchScout** — see Centerpieces section above. Drove all PM artifacts: PRD, ICP, eval plan, two-arm experimental design.
- **Onemyle User Chatbot** — AI-powered local area intelligence assistant for Indian cities. Designed a 3-node deployment with local Gemma orchestrator, ChromaDB semantic cache, multi-LLM parallel calls (Claude · GPT-4o · Gemini), intent-based routing, and a FastAPI + React stack.
- Strategic input on roadmap, ICP refinement, AI product positioning, category taxonomy design.

### Principal Program Manager · Oracle Cloud Infrastructure (OCI)
*Fremont, CA · Jan 2026 – Mar 2026*

- Led **Fiber Supply Remediation Program** for hyperscale data center builds; expanded qualified supplier base from 3 to 7 vendors; instituted recurring demand–supply alignment cadence with Stargate DC delivery; built a lightweight estimation tool for bulk fiber forecasting.

### Manager, Technical Program Management · Apple Inc.
*Infrastructure Programs · Software Tools for PMO and DC Operations*
*Sunnyvale, CA · Apr 2011 – Jan 2024*

- Led multi-year infrastructure programs across compute, storage, network, data center, on-prem cloud, security, and big data; managed a team of EPMs on cross-functional initiatives.
- **Managed capital budgets exceeding $20M** for infrastructure programs; drove **50% efficiency gain** in program tracking via a custom-built PMO portal and DC operations prioritization tool.
- Consolidated **400+ applications** from high-cost third-party data centers into Apple-owned facilities, achieving multi-million-dollar annual cost savings.
- Met **PCI-DSS standards** for retail and payments workloads via isolated High-Secure Environments (HSEs); owned infrastructure readiness for major product-launch surges.
- **Agile delivery cadence** across cross-functional teams (Network Engineering, Platform/Cloud SRE, Database Engineering, Storage, DC Ops, Apple Pay, Apple Online Store, iCloud, AML).

### Prior Experience (Summary)

PayPal (Senior PM, Site Operations & InfoSec, contract, 2010–11) · EDS/HP Enterprise Services (Delivery Manager, 125+ team, 2007–10) · Bank of America (Release Manager, 2006–07) · iDrive Inc. (CTO, 1998–2006, designed a commercially successful backup product).

---

## AI / ML SKILLS

- **LLM APIs:** Anthropic Claude (sonnet-4.6, opus-4.7) · OpenAI GPT-4o · Google Gemini · function calling · tool_use · streaming
- **Agent Frameworks:** LangGraph (StateGraph, Send API, HITL, checkpointing) · LangChain (LCEL, Runnables) · CrewAI (parallel + hierarchical) · Mem0
- **Protocols:** Model Context Protocol (MCP) — tools, resources, prompt templates, streamable-http; FastMCP server + agentic clients
- **Patterns:** Tool-use loops · ReAct · reflection/self-critique · orchestrator-worker · multi-agent crews · arm-routed treatment design
- **RAG:** Embeddings (sentence-transformers, BERT, OpenAI text-embedding-3) · chunking strategies · cosine similarity · citation grounding
- **Vector Stores:** ChromaDB · Qdrant · Pinecone (familiar)
- **Validation & Schema:** Pydantic v2 · TypedDict · structured output · fence-tolerant JSON parsing
- **Async:** asyncio · asyncio.gather · async context managers · topological scheduling (HPRC)
- **Observability & Eval:** LangSmith (`@traceable`, `get_current_run_tree`, span hierarchy, trace-URL drill-down) · outcome-based A/B with p-value significance testing · per-call USD cost tracking from token usage · LangFuse (in progress)
- **Testing & CI:** pytest · GitHub Actions schema smoke gating
- **PM rigor for AI:** PRD · ICP/anti-ICP · eval plan · GTM brief · risk register · two-arm experimental design · prompt-version A/B

---

## CAPSTONE PROJECTS

- **StockSage MCP Server** *(FastMCP · Claude · ChromaDB)* — Production MCP server exposing 4 stock-analysis tools (price, news sentiment, fundamentals, earnings RAG) over streamable-http; agentic loop with dynamic tool discovery and persistent vector store for earnings transcripts.
- **ReviewCrew** *(CrewAI · GitHub API · Claude)* — 2-agent CrewAI crew (code reviewer + security reviewer) analyzing GitHub PRs in parallel via `Process.parallel`; human-in-the-loop before posting comments.
- **ResearchBot** *(LangGraph · Kafka · DuckDuckGo)* — Multi-step web-research agent with typed `StateGraph`, conditional edges, `MemorySaver` checkpointing, and HITL `interrupt()`/`update_state()`.
- **DocTalk** *(LangChain · Qdrant · sentence-transformers · Claude)* — End-to-end RAG over PDFs with citation tracking (page numbers preserved through chunking).
- **ToolBot** *(asyncio · Pydantic v2 · Claude/OpenAI/Gemini)* — Unified CLI agent supporting all three major LLMs behind a single tool-use loop with streaming and multi-turn memory.

---

## LINKS

- LinkedIn: [linkedin.com/in/rvrajesh123](https://linkedin.com/in/rvrajesh123/)
- GitHub org (AI projects): [github.com/Agentic-and-AI-Engineering-Projects](https://github.com/Agentic-and-AI-Engineering-Projects)
- AI Engineering Curriculum: [ai_engineer_program](https://github.com/Agentic-and-AI-Engineering-Projects/ai_engineer_program)
- MatchScout: [Onemyle-matchscout](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout)
- HPRC Framework: [github.com/HPRCFramework/hprc-framework](https://github.com/HPRCFramework/hprc-framework) · [hprcframework.dev](https://hprcframework.dev)
