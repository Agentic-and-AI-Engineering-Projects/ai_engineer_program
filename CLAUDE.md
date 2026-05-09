# AI Engineer Program — Claude Context

## What This Is
A project-based 4-month self-training curriculum to become an Agentic AI Engineer.
Claude acts as trainer/guide — building every project together, explaining concepts inline.
No passive video courses — learning by doing, with deeplearning.ai shorts on-demand as needed.

## The Person
- Rajesh Ramani, 54, program manager background (infrastructure domain, Apple)
- CS degree 1989, languages: C, C++, PHP, decent Python, web apps
- AWS Certified Solutions Architect Associate
- 15+ years away from core dev, returning now
- Real-world agentic work at Onemyle startup (augments this training)
- Goal: Agentic AI Engineer positions within 4 months (by ~July 2026)

## Kanban Tracking
- Tool: MyKanban at http://192.168.1.156:3002
- Project: "AI Engineering Readiness" (Project ID: 3)
- Login: see local credentials (not committed)
- Tickets: #17–#73 (growing)
- Move tickets: Backlog → Todo → In Progress → Done as work progresses

## Python Environment
- Repo: ~/ai/ai_engineer_program/
- Venv: ~/ai/ai_engineer_program/.venv/
- Activate: source .venv/bin/activate
- Keys: copy .env.example to .env, add ANTHROPIC_API_KEY etc.

## The 14-Project Curriculum (v6 — updated 2026-04-29)

### v6 Changes (driven by real Oracle/Salesforce/Adobe/Airwallex job postings)
- **P7 expanded**: + Ragas, DeepEval, Promptfoo eval frameworks (#79)
- **P10 expanded**: + FastAPI wrapper, Pinecone, multi-cloud LLM routing, reliability patterns, cost tracking (#74-#78)
- **P12 NEW**: Multi-agent framework showdown — AutoGen vs LangGraph vs CrewAI (#80)

### Business Domain Theme: Enterprise Customer Operations
P7–P11 follow a coherent real-world domain: a suite of agents for customer operations.
Uses Faker for synthetic customer data. Connects naturally to Onemyle's real work.

| # | Folder | Project | Key Tech | Kanban Tickets | Month |
|---|--------|---------|----------|----------------|-------|
| P1 | p1_toolbot | ToolBot — CLI agent, 3 LLMs | async, Pydantic v2, tool_use, streaming | #17–20 | 1 |
| P2 | p2_doctalk | DocTalk — PDF Q&A + citations | Embeddings, Chroma→Qdrant, RAG, LangChain | #21–24 | 1 |
| P3 | p3_researchbot | ResearchBot — multi-step web research | LangGraph, checkpointing, human-in-loop, A2A intro | #25–28 | 2 |
| P3-Adv | p3_adv_langgraph | Advanced LangGraph — Send API, Orchestrator-Worker | Send API, Flow Engineering, Temporal+LangGraph | #72 | after P6 |
| P4 | p4_stocksage | StockSage — stock analysis agent | Multi-agent, Mem0 memory, reasoning model selection | #29–33 | 2 |
| P5 | p5_reviewcrew | ReviewCrew — GitHub PR reviewer | CrewAI, parallel execution, hierarchical agents | #34–36 | 3 |
| P6 | p6_mcp | MCP++ + A2A — Onemyle MCP server | MCP spec, streamable-http, OAuth 2.1, A2A protocol | #37–39, #73 | 3 |
| P7 | matchscout-onemyle | **MatchScout — Onemyle Marketplace PoC** (replaces ChurnGuard) | 3-stage cascade (rules + vector + LLM), LangGraph, sentence-transformers, Ragas, DeepEval, Promptfoo, LangSmith, LangFuse | #87 (replaces #40-42, #79) | 3 |
| P8 | p8_security | PII Compliance Agent — agent security | OWASP LLM Top 10, PII detection, NeMo Guardrails | #48 | 3 |
| P9 | p9_memory | Account Memory Agent — long-term memory | Zep (Graphiti), Mem0, temporal knowledge graphs | #49 | 3–4 |
| P10 | p10_platform | AgentPlatform — production deploy | Docker, k3s, GitHub Actions, AWS Bedrock, Terraform, **FastAPI, Pinecone, multi-cloud routing, reliability patterns, cost tracking** | #43–45, **#74–78** | 4 |
| P11 | p11_multimodal | Contract & Invoice Analyzer — vision | Claude vision, PyMuPDF, multi-modal RAG, GPT-4o | #50 | 4 |
| **P12 NEW** | p12_framework_showdown | Multi-agent framework comparison | **AutoGen vs LangGraph vs CrewAI**, comparison blog | **#80** | 4 |

## Supplementary Tickets (non-blocking)
- #67 — Raw ReAct Loop (react_agent.py)
- #68 — Reflection / Self-Critique Pattern
- #69 — Python Fundamentals for AI Engineering
- #70 — Python Refresher (lambdas, decorators, async, *, **, context managers, ABC)
- #71 — P5 ReviewCrew: Hierarchical process (manager agent)

## Concepts Covered (by project)
- P1: async/await, Pydantic v2, tool_use loop, streaming, system prompts, context management
- P2: embeddings, cosine similarity, chunking strategies, RAG pipeline, LangChain abstractions
- P3: LangGraph StateGraph, typed state, nodes/edges, checkpointing, human-in-the-loop
- P3-Adv: Send API, orchestrator-worker, flow engineering, Temporal+LangGraph, state management failures
- P4: multi-tool orchestration, structured output, domain RAG, agent synthesis, financial APIs
- P5: CrewAI agents/tasks/crew, agent specialization, parallel execution, hierarchical agents
- P6: MCP spec, streamable-http transport, tool schemas, resource protocol, OAuth 2.1, A2A protocol
- P7 (MatchScout — Onemyle PoC): **3-stage cascade architecture (rules filter → vector similarity → LLM agent)**, LangGraph state machine, sentence-transformers for embeddings/vector ranking, Faker for synthetic marketplace data, LangSmith tracing, LangFuse dashboards, **Ragas (faithfulness/groundedness), DeepEval (LLM unit tests), Promptfoo (A/B testing), regression suite gating CI**, two-sided marketplace product thinking, category taxonomy + adjacency design, cold-start awareness, marketplace fairness considerations
- P8: OWASP LLM Top 10, PII detection, prompt injection blocking, NeMo Guardrails, audit trails
- P9: Zep temporal knowledge graphs, Mem0 semantic facts, LongMemEval benchmark comparison
- P10: Docker multi-stage builds, k8s manifests, secrets management, GitHub Actions CI/CD, Bedrock, **FastAPI + SSE streaming, Pinecone migration from Chroma, multi-cloud LLM routing (Bedrock + Azure OpenAI + GCP Vertex), reliability patterns (tenacity exponential backoff, pybreaker circuit breaker, automatic provider fallback), per-request token + USD cost tracking with budget alerts**
- P11: PyMuPDF page rendering, Claude vision API, base64 image content blocks, multi-modal RAG
- **P12: AutoGen conversational multi-agent pattern, framework comparison methodology (LoC, latency, cost, debuggability), technical writing for LinkedIn**

## P7 → MatchScout Pivot (2026-05-09)

P7 was originally "ChurnGuard" — a synthetic SaaS churn prediction agent.
Pivoted to **MatchScout** — a real Onemyle initiative with the same learning
objectives but framed as a formal pro bono PoC at Onemyle (where Rajesh is
an angel investor + pro bono Product/AI Lead).

**Why pivot:** ChurnGuard would have been a hobby project on the resume.
MatchScout is a formal Onemyle initiative — credible, real, defensible in
interviews. Same technical learning + marketplace AI patterns added.

**MatchScout = AI match-quality predictor for Onemyle's two-sided marketplace** (creators ↔ local businesses). 3-stage cascade architecture (rules filter → vector similarity → LLM agent) covering everything ChurnGuard would have taught, plus marketplace AI patterns.

**Status:** PoC. Synthetic data. Productionization pending Onemyle roadmap.

**Replaces:** P7 #40, #41, #42, #79 (those tickets superseded). PM artifact ticket (was #81) is incorporated into MatchScout deliverables.

**New ticket:** #87 — MatchScout — Onemyle Marketplace PoC.

**Design doc:** `matchscout-onemyle/DESIGN.html` (architecture, data flow, runtime model)

## Path B — AI Product Management Track (added 2026-05-01)

Parallel PM artifact track integrated into P7-P12. Modern Agile/Lean approach (no waterfall PMP-style docs).
Each remaining project produces 1-page artifacts alongside the engineering work.

### Templates (in `p0_pm_templates/`)
- 1-page PRD · ICP · Eval Plan · GTM Brief · Risk Register · Working Backwards PR · Buy-vs-Build

### Reference Doc
- `p0_pm_templates/ai_product_management.html` — comprehensive AI PM reference: terminology, frameworks, AI-specific concepts, interview prep, project log appendix that grows per project

### PM Artifacts per Project (Kanban tickets #81-#86)

| # | Project | Artifacts |
|---|---------|-----------|
| #81 | P7 Customer Health | PRD + ICP + Eval Plan + GTM Brief |
| #82 | P8 PII Compliance | PRD + ICP + Eval Plan + Risk Register |
| #83 | P9 Account Memory | PRD + ICP + Eval Plan + GTM Brief + Working Backwards |
| #84 | P10 AgentPlatform | PRD + ICP + GTM Brief + Risk Register + Working Backwards + Buy-vs-Build |
| #85 | P11 Contract Analyzer | PRD + ICP + Eval Plan + GTM Brief + Risk Register |
| #86 | P12 Framework Showdown | Decision Framework + LinkedIn blog (research project, different artifacts) |

### Workflow per project
1. Finish engineering work (existing tickets)
2. Open PM ticket (#81+) → copy templates into `pX_xxx/pm/` folder
3. Fill in artifacts (~1-2 hours per project)
4. Review for AI-PM-specific framing (eval criteria, cost-per-task, hallucination budget, ICP/anti-ICP rigor)
5. Mark ticket Done

### Why Path B (not parallel PM curriculum)
- Same projects → two evidence stacks (engineering portfolio + PM artifacts)
- Path A (sequential) delays PM positioning by ~3 months
- Path C (parallel curriculum) doesn't compound — one-shot artifacts vs growing codebase
- Path B leverages Apple TPM background + Onemyle "Product Consultant" role + RAFL patent
- Targets unicorn profile: AI Engineer + AI PM (most candidates are one or the other)

## Training Resources (on-demand, not upfront)
| Course | Platform | When to use |
|--------|----------|-------------|
| LangChain for LLM Application Development — Andrew Ng | deeplearning.ai | Before P2 |
| AI Agents in LangGraph | deeplearning.ai | Before P3 |
| Multi-Agent Systems with CrewAI | deeplearning.ai | Before P5 |
| Evaluating and Debugging Generative AI | deeplearning.ai | Before P7 |
| Complete Agentic AI Engineering Course | Udemy (owned) | Reference throughout |

## LLM Coverage
All three major LLMs are used across the curriculum — not Claude-only:
- **Anthropic Claude** (claude-sonnet-4-6 / claude-opus-4-7) — primary, tool_use, MCP, vision
- **OpenAI** (gpt-4o) — function calling, multi-modal comparison
- **Google Gemini** — function calling, multi-modal
All three API keys are in .env: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY

## Claude's Role as Trainer
- Give Rajesh coding goals — let him write the code, then review and correct inline
- Do NOT scaffold everything — only scaffold to unblock, not replace the learning
- Explain every concept as it appears in real code (not abstract)
- Give daily tasks sized for ~2–3 hours of focused work
- Point to deeplearning.ai shorts only when concept needs lecture reinforcement
- Move Kanban tickets as milestones are hit
- Run a 5–8 question quiz at end of EVERY project before moving to the next one

## Training Style (Non-negotiable)
1. **Interactive coding** — Give a goal + any needed context/signature. Rajesh writes it. Review after.
2. **End-of-project quiz** — Before starting next project, quiz on concepts from the one just completed.
   Questions should reference actual code from the project, not abstract theory.
3. **Detailed step-by-step instructions** — For every coding task, give numbered steps with: what to write, what it does, why it's needed. Include code snippets per step. Not high-level bullets.

## Daily Plan Structure
Each session: Claude gives the day's task, Rajesh codes it, concepts explained inline.
Weekly plan tickets in Kanban track the week's goals.

## Current Status (as of 2026-04-26)
- [x] P1 ToolBot — COMPLETE (Tickets #17-20, quiz 7/7)
- [x] P2 DocTalk — COMPLETE (Tickets #21-24, quiz 6.5/8)
- [x] P3 ResearchBot — COMPLETE (Tickets #25-27, #65, #66, quiz 6.5/7)
- [x] P4 StockSage — COMPLETE (Tickets #29-33, quiz 6.5/8)
- [x] P5 ReviewCrew — COMPLETE (Tickets #34-36, quiz 6/6)
- [ ] P6 MCP++ — IN PROGRESS (Ticket #37 in progress)
  - [x] server_intro.py — FastMCP server, streamable-http, get_stock_price tool
  - [x] client_intro.py — async client, asyncio.gather for concurrent calls
  - [ ] Resources + prompt templates (#38)
  - [ ] StockSage tools as MCP server + OAuth 2.1 (#39, #73)

## Related Projects
- Onemyle / reel-analysis-lib: ~/ai/Onemyle/reel-analysis-lib (real-world agent deployment)
- MyKanban: ~/ai/mykanban (the Kanban tool used to track this program)
- Onemyle MCP server: related to P6 MCP++ project
