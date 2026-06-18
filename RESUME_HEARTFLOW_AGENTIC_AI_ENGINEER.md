# RAJESH RAMANI
**Agentic AI Engineer**
Fremont, CA, USA
rajesh_ramani@icloud.com · (408) 806-0359
[linkedin.com/in/rvrajesh123](https://linkedin.com/in/rvrajesh123/) · [github.com/rrvenkatrama](https://github.com/rrvenkatrama/)

---

## PROFILE SUMMARY

Apple Alum and Agentic AI Engineering Consultant with a background in enterprise program leadership and hands-on AI product development. After years leading large-scale infrastructure programs, I deliberately transitioned into agentic AI, spending the past several months building and shipping production AI systems end to end. Currently an investor and Agentic AI Product Consultant for a hyperlocal creator marketplace startup, where I built **MatchScout**, an AI recommender that matches businesses with creators and is evaluated against real gig outcomes. Creator of the open-source **HPRC Framework**, an AI-native server-side templating engine. Experienced at bridging business, product, engineering, and AI teams, turning ambiguous problems into practical solutions with measurable impact.

---

## ENGINEERING CENTERPIECES

### HPRC Framework — Open-Source AI-Native Templating Engine
*Python · Apache-2.0 · asyncio · Pydantic v2 · FastAPI · pytest*
GitHub: [github.com/HPRCFramework/hprc-framework](https://github.com/HPRCFramework/hprc-framework) · Web: [hprcframework.dev](https://hprcframework.dev)

- **Project Overview:** Designed and built HPRC end-to-end — a server-side templating engine that lets developers embed LLM prompts directly inside HTML and runs them automatically when the page is rendered.
- **Render Pipeline:** Figures out which prompts depend on which others, runs the independent ones concurrently, and caches the results so repeat renders are fast.
- **Multi-Provider LLM Layer:** Six interchangeable adapters (OpenAI, Anthropic, Gemini, Ollama/LM-Studio, Mock, and a multi-provider router) behind one simple interface. Each provider's SDK is loaded only when used.
- **Safe Extension Points:** External rules and allowlisted tool calls expose seams for customization without an expression language inside templates, so templates can't be turned into arbitrary code.
- **Architecture:** Clean layered design with Pydantic v2 throughout and a tolerant HTML parser.
- **Language Specification:** Authored the SPREP language specification (a mini-RFC) that defines the embedded-prompt syntax.

### MatchScout — Onemyle Marketplace AI Recommender (PoC)
*LangGraph · Claude Sonnet 4.6 · sentence-transformers · SQLite · Streamlit · LangSmith · pytest · GitHub Actions*
GitHub: [Onemyle-matchscout](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout)

- **Pipeline Architecture:** Built the entire recommender as a single LangGraph state machine: a rules-based filter narrows candidates, a sentence-transformer cosine ranker scores them, and a treatment-arm router decides whether the final pick is made by the rules baseline or by Claude using past-gig metrics and a versioned prompt.
- **Outcome-Based Evaluation:** 50% of gigs flow through a no-LLM control, 50% through the Claude re-ranker, and per-arm quality is measured on real downstream gig outcomes with p-value significance testing. No synthetic golden set; no LLM-as-judge.
- **Guardrails and Validation:** Bounded retry loop on LLM validation failure (malformed JSON, wrong cardinality, hallucinated creator IDs); structured-output enforcement keeps emit shape stable for downstream processing.
- **Prompts as Tuning Surface:** Versioned prompt files, every recommendation tagged with the prompt version, dashboard segments quality and cost by version so prompt iteration is empirically driven.
- **Observability:** LangSmith tracing on every LLM call. Trace URLs persisted alongside each recommendation so a single click in the dashboard opens the corresponding trace.
- **Cost Tracking:** Per-call USD cost computed from token usage and persisted on each recommendation, enabling cost-per-arm and cost-per-prompt-version comparison.
- **CI:** Smoke test on every push via GitHub Actions, exercising the no-LLM path (no API key required).

---

## AI / ML SKILLS

- **LLM APIs:** Anthropic Claude (sonnet-4.6, opus-4.7) · OpenAI GPT-4o · Google Gemini · function calling · tool_use · streaming · prompt caching · extended thinking
- **Agent Frameworks:** LangGraph (StateGraph, Send API, HITL, MemorySaver, SqliteSaver) · LangChain (LCEL Runnables, ChatPromptTemplate, RunnableParallel/Branch/Passthrough/Lambda) · CrewAI (parallel + hierarchical) · Claude Agent SDK · Mem0
- **Protocols:** Model Context Protocol (MCP) — tools, resources, prompt templates, streamable-http; FastMCP server + agentic clients
- **Agentic Patterns:** Tool-use loops · ReAct · reflection / self-critique (Reflexion) · orchestrator-worker · hub-and-spoke · multi-agent crews · subagent decomposition · human-in-the-loop · arm-routed treatment design
- **RAG:** Embeddings (sentence-transformers, OpenAI text-embedding-3) · RecursiveCharacterTextSplitter separator hierarchy · cosine similarity · L2-normalization → dot-product optimization · citation grounding · metadata propagation through chunkers
- **Vector Stores:** ChromaDB (Ephemeral + Persistent) · Qdrant
- **Memory:** Mem0 semantic memory · checkpointing (MemorySaver, SqliteSaver) · Anthropic Memory tool · Letta (planned, P9)
- **Evaluation & Guardrails:** Outcome-based two-arm A/B with p-value significance · per-call USD cost tracking from token usage · LLM-as-judge bias awareness (position / verbosity / self-preference / style / drift / preference leakage) · gold-set construction · structured-output grading · bounded retry on validation failure
- **Validation:** Pydantic v2 · TypedDict · structured output
- **Observability:** LangSmith (@traceable decorator, span hierarchy, trace-URL drill-down from dashboards) · LangFuse (in progress)
- **Cloud & Backend:** Python · FastAPI · SQLite · asyncio · REST API design · AWS (Solutions Architect Associate certified)
- **Testing & CI:** pytest · GitHub Actions

---

## PROFESSIONAL EXPERIENCE

### Investor / Agentic AI Product Consultant — Onemyle (Hyperlocal Creator/Business Marketplace Startup)
*Remote · Mar 2026 – Present*

- **AI Strategy & Architecture:** Lead AI strategy, technical architecture, and product direction for the startup. Currently designing and shipping **MatchScout** (see Engineering Centerpieces).
- **Onemyle User Chatbot:** Designed an AI-powered local-area assistant for Indian cities — a 3-node deployment with a local Gemma orchestrator, ChromaDB semantic cache, multi-LLM parallel calls (Claude · GPT-4o · Gemini), intent-based routing, and a FastAPI + React stack.
- **Product Direction:** Strategic input on roadmap, ICP refinement, AI product positioning, and category taxonomy design.

### Principal Program Manager — Oracle Cloud Infrastructure (OCI)
*Fremont, CA · Jan 2026 – Mar 2026*

- **Fiber Supply Remediation Program:** Established and led a cross-functional program to resolve bulk fiber supply constraints impacting hyperscale data center builds.
- **Supplier Diversification:** Expanded fiber supplier base from 3 to 7 vendors, reducing supply risk and improving resilience for large-scale data center deployments.
- **Planning Tool:** Developed a lightweight bulk-fiber estimation tool and defined processes enabling colocation providers to leverage Oracle supply allocations.

### Manager, Technical Program Management — Apple Inc.
*Infrastructure Programs · Software Tools for PMO and DC Operations · Sunnyvale, CA · Apr 2011 – Jan 2024*

- **Program Leadership:** Led multi-year infrastructure programs across compute, storage, network, on-prem cloud, big-data, and database environments at hyperscale, ensuring quality, consistency, and integrity across cost-optimization, automation, and cross-functional collaboration initiatives.
- **Data-Driven PMO Tooling:** Built and shipped a custom PMO portal and a DC operations prioritization tool (DCCP) that drove a **50% efficiency gain** in cross-org program tracking and automated reporting.
- **Budgeting & Capital Planning:** Managed capital budgets exceeding **$20M** for large-scale infrastructure programs; established CapEx tracking mechanisms and partnered with finance and vendor management on right-sizing and optimization.
- **Cost Savings & Consolidation:** Achieved multi-million-dollar cost savings by consolidating 400+ applications from high-cost data centers to Apple-owned facilities; drove decommissioning programs to recover power, space, and cost.
- **Security & Compliance:** Met PCI security standards for critical retail applications by establishing PCI-compliant High-Secure Environments (HSEs) in collaboration with compliance, information security, and network/systems architecture teams.
- **Cross-Functional Partnerships:** Network Engineering · Platform/Cloud SRE · Database Engineering · Storage Engineering · DC Operations · Apple Online Store · Apple Pay · Retail Apps · iCloud · Applied Machine Learning.

---

## PRIOR EXPERIENCE SUMMARY

- **Senior Project Manager, Site Operations and Information Security, PayPal (Aug 2010 – Feb 2011) (Contract)**
Implemented information security solutions in collaboration with PayPal's Information Risk and Security organization (IRM), data center site operations, and platform SRE teams. Protected digital assets through DDoS prevention, hardware security modules (HSMs), bastion infrastructure, and real-time traffic analysis systems for fraud detection and prevention.
- **Delivery Manager, IT Infrastructure Services, EDS/HP Enterprise Services, Chennai, India (2007–2010)**
Led a 125+ member team providing 24/7 L1/L2 incident management and service delivery across infrastructure services, including compute, backups, identity and access management, and storage.
- **Release Manager, Bank of America, Agoura Hills, CA (2006–2007)**
Managed and coordinated the deployment of releases for a loan origination system development project.
- **Chief Technology Officer, iDrive Inc., Woodland Hills, CA (1998–2006)**
Designed and led the end-to-end development of a commercially successful data backup product, owning architecture, engineering, and roadmap through eight years of product evolution.

---

## CAPSTONE PROJECTS

Built across a focused 4-month agentic AI curriculum to demonstrate framework breadth and pattern coverage.

- **StockSage MCP Server** *(FastMCP · Claude · ChromaDB · sentence-transformers)* — MCP server with 4 stock-analysis tools over streamable-http. Generic agentic loop dispatches tools dynamically with zero hardcoding. Persistent ChromaDB vector store for earnings-transcript embeddings; MCP prompt templates decoupled from client.
- **ReviewCrew** *(CrewAI · GitHub REST API · Claude)* — 2-agent crew (code reviewer + security reviewer) analyzing GitHub PRs in parallel. Custom GitHub tool integration; human-in-the-loop approval before comment posting.
- **ResearchBot** *(LangGraph · Kafka · DuckDuckGo)* — Multi-step web-research agent on a LangGraph state graph with typed state, conditional edges, and checkpointing. Human-in-the-loop interrupt and resume for mid-graph approval.
- **DocTalk** *(LangChain · Qdrant · sentence-transformers · Claude)* — End-to-end RAG pipeline over PDFs: ingestion, chunking, embedding, cosine retrieval, and cited answer generation. Per-page metadata propagation through the chunker enables citation grounding.
- **ToolBot** *(asyncio · Pydantic v2 · Anthropic / OpenAI / Gemini)* — Unified multi-LLM CLI agent behind a single tool-use loop. Streaming, multi-turn memory with sliding-window truncation, provider-specific dialect handling, Pydantic v2 schema validation.

---

## EDUCATION & CERTIFICATIONS

- M.S., Information Systems — California State University, Los Angeles
- B.S., Computer Science — National Institute of Technology, India
- **AWS Solutions Architect — Associate** · **KCNA** · **PMI-PMP** · **Certified ScrumMaster** · **GCP Cloud Digital Leader**

---

## LINKS

- LinkedIn: [linkedin.com/in/rvrajesh123](https://linkedin.com/in/rvrajesh123/)
- GitHub org (AI projects): [github.com/Agentic-and-AI-Engineering-Projects](https://github.com/Agentic-and-AI-Engineering-Projects)
- AI Engineering Curriculum: [ai_engineer_program](https://github.com/Agentic-and-AI-Engineering-Projects/ai_engineer_program)
- MatchScout: [Onemyle-matchscout](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout)
- HPRC Framework: [github.com/HPRCFramework/hprc-framework](https://github.com/HPRCFramework/hprc-framework) · [hprcframework.dev](https://hprcframework.dev)
