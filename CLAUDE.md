# AI Engineer Program — Claude Context

## What This Is
A project-based 4-month self-training curriculum to become an Agentic AI Engineer.
Claude acts as trainer/guide — building every project together, explaining concepts inline.
No passive video courses — learning by doing, with deeplearning.ai shorts on-demand as needed.

## The Person
- Rajesh Ramani, 54, program manager background (infrastructure domain, Apple)
- CS degree 1989, languages: C, C++, PHP, Python (now primary)
- AWS Certified Solutions Architect Associate · PMI-PMP · KCNA · GCP CDL · CSM
- 15+ years away from core dev when starting this program; now returning as hands-on builder
- Real-world agentic work as Investor / Agentic AI Product Consultant at Onemyle startup
- Open-source author: HPRC Framework (Apache-2.0)
- **Identity hook (locked in resumes 2026-06-17):** "Apple Alum and Agentic AI Engineering Consultant"
- **Goal (active since 2026-05-27):** Agentic AI Engineer roles primary, AI Program Management roles secondary. Open to mid-IC salary for practical agentic AI experience.

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

## The 15-Project Curriculum (v8 — refreshed 2026-05-13 for frontier coverage)

### v8 Changes (driven by 2026 frontier agent stack)
- **P9 expanded + pinned to MatchScout V2** (refined 2026-05-13): 4-framework memory benchmark (Zep + Mem0 + Anthropic Memory tool + Letta) on MatchScout V2's actual memory workload — distilled business prefs + creator personas + pattern memory + reflexion memory + LLM bypass. ~78% input-token reduction over V1.
- **P12 expanded**: + Claude Agent SDK + OpenAI Agents SDK to the framework comparison (now 5 frameworks)
- **P13 (v8.2 refined 2026-05-13)**: Pinned to MatchScout V2. Agent SDK rebuild of Stage 3 with subagents (history/reasoner/fact-checker/critic). Memory + subagents work multiplicatively for V2.

### v7 Changes (locked 2026-05-10)
- **P7 pivoted**: ChurnGuard → MatchScout (Onemyle marketplace PoC, gig-driven recommender)

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
| P7 | [Onemyle-matchscout](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout) (separate repo since 2026-06-08) | **MatchScout — Onemyle Marketplace PoC** (gig-driven recommender, two-arm outcome A/B) | 3 stages × 2 arms (rules + vector cosine + LLM re-ranker on top 10), Gig + CreatorRecommendation entities, SQLite, Streamlit dashboard, LangGraph, sentence-transformers, versioned prompt templates, scipy chi-squared, Ragas/DeepEval/Promptfoo/LangSmith/LangFuse as dev-time tools (no CI eval gate), pytest schema smoke test | #87 (replaces #40-42, #79) | 3 |
| P8 | p8_security | PII Compliance Agent — agent security | OWASP LLM Top 10, PII detection, NeMo Guardrails | #48 | 3 |
| P9 | p9_memory | **MatchScout V2 memory layer** — 4-framework benchmark (Zep + Mem0 + Anthropic Memory tool + Letta) on MatchScout's actual memory workload | Distilled business preferences, creator personas, pattern memory, reflexion memory, LLM bypass. ~78% input-token reduction vs V1. | #49 | 3–4 |
| P10 | p10_platform | AgentPlatform — production deploy | Docker, k3s, GitHub Actions, AWS Bedrock, Terraform, **FastAPI, Pinecone, multi-cloud routing, reliability patterns, cost tracking** | #43–45, **#74–78** | 4 |
| P11 | p11_multimodal | Contract & Invoice Analyzer — vision | Claude vision, PyMuPDF, multi-modal RAG, GPT-4o | #50 | 4 |
| **P13** | p13_matchscout_v2_agentsdk | **MatchScout V2 — Agent SDK rebuild of Stage 3** (subagents + Anthropic Memory tool + Reflexion) — pinned to MatchScout V2, not academic research bot | Claude Agent SDK, subagents (history/reasoner/fact-checker/critic), Anthropic Memory tool, Reflexion. Inline hallucination guard via fact-checker subagent. | #88 | 4 |
| **P14** | p14_managed_agents | **MatchScout V3 — Claude Managed Agents (cloud-runtime rebuild of Stage 3)** — same workload as P13 but on Anthropic's managed agent runtime instead of local SDK. End artifact: head-to-head comparison of managed vs local-SDK (cost/latency/dev velocity/ops burden/control surface). | Anthropic Managed Agents API, Claude Files API, task submission + polling + streaming events, managed memory persistence, tool callbacks. | #89 | 4 |
| P12 (expanded) | p12_framework_showdown | Multi-agent framework comparison (5 frameworks) | **AutoGen + LangGraph + CrewAI + Claude Agent SDK + OpenAI Agents SDK**, comparison blog | **#80** | 4 |

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
- P7 (MatchScout — Onemyle PoC, gig-driven recommender): **gig-driven 3-stage pipeline × 2-arm outcome A/B** (Arm 1 = 10% no-LLM control taking top 3 by cosine; Arm 2 = 90% LLM ranks top 3 from top 10 using a versioned prompt template + past-gig metrics). Stage 1 rules = location · budget · content_type overlap. Stage 2 vector cosine over (niche_tags + profile_description + categories + subcategories). Stage 3 = LangGraph state machine with single versioned prompt. Profile descriptions are stored fields (Instagram-bio style), synthesized via Claude one-time. Storage: CSV for catalog, SQLite for gigs/recommendations/past_gigs. Streamlit dashboard with chi-squared significance. Eval is **outcome-based only** — no synthetic golden set, no CI quality gate (pytest schema smoke test only). Ragas/DeepEval/Promptfoo are **dev-time tools** for prompt iteration, not CI blockers. LangSmith tracing per recommendation, LangFuse rolling dashboards. Versioned prompt templates (prompts/arm2_v1.txt) with `prompt_version` stamped on each recommendation — enables A/B-ing prompts against outcomes. Two-sided marketplace product thinking, treatment-arm experimental design, statistical significance reasoning, prompt-as-tuning-surface, gig-as-unit-of-work primitive
- P8: OWASP LLM Top 10, PII detection, prompt injection blocking, NeMo Guardrails, audit trails
- P9 (v8.1 refined 2026-05-13): **MatchScout V2 memory layer — 4-framework benchmark on MatchScout's actual workload.** V1 re-feeds raw past-gig history every recommendation (~5K tokens/gig). V2 introduces a memory layer: distilled business preferences ("biz_042 rejects >100K followers"), distilled creator personas ("creator_017 reliable, 8/10 successful"), pattern memory ("Italian fine-dining + natural_lighting tag → 87% success"), reflexion memory (LLM's self-critiques as guardrails), and LLM bypass for high-confidence memory consensus. Same workload implemented with all 4 frameworks: (1) Zep/Graphiti temporal graphs, (2) Mem0 semantic facts, (3) Anthropic Memory tool native primitive, (4) Letta virtual context management. Measured on real MatchScout V1 outcome data — recall accuracy, latency, cost-per-gig, persistence at scale, cold-start handling. Expected gains: ~78% input-token reduction, ~73% LLM-cost reduction, ~50% latency reduction. End artifact: memory framework recommendation for MatchScout V2 + comparison blog.
- P10: Docker multi-stage builds, k8s manifests, secrets management, GitHub Actions CI/CD, Bedrock, **FastAPI + SSE streaming, Pinecone migration from Chroma, multi-cloud LLM routing (Bedrock + Azure OpenAI + GCP Vertex), reliability patterns (tenacity exponential backoff, pybreaker circuit breaker, automatic provider fallback), per-request token + USD cost tracking with budget alerts**
- P11: PyMuPDF page rendering, Claude vision API, base64 image content blocks, multi-modal RAG
- **P13 (v8.2 refined 2026-05-13): MatchScout V2 — Agent SDK rebuild of Stage 3.** Replaces V1's single LangGraph LLM call with a subagent decomposition: (1) history/context subagent reads from P9's memory layer, (2) reasoner subagent picks top 3, (3) **fact-checker subagent catches hallucinations inline** (validates cited past_gigs exist in DB before emitting), (4) critic subagent (Reflexion) reviews + writes self-critiques into reflexion memory. Memory + subagents are multiplicative: memory makes subagents affordable (each reads compact slice ~400 tokens), subagents target memory access. Net V2 (memory + subagents) vs V1: similar cost (5 calls × small context ≈ 1 call × big context), materially better quality (inline fact-check + Reflexion + personalization). Same domain as P7/P9 → coherent portfolio: one product, two technical investigations for V2.
- **P14 (v8.3 NEW 2026-06-01): MatchScout V3 — Claude Managed Agents (cloud-runtime rebuild of Stage 3).** Same workload as P13, rebuilt on Anthropic's managed agent runtime instead of local SDK. POST a task → Anthropic owns compute, state, tool execution. End artifact: head-to-head comparison matrix (managed vs local SDK) — cost per task, p50/p95 latency, dev velocity, ops burden, control surface, observability. Portfolio narrative: "I built the same agent on the local SDK and the managed runtime — here's the tradeoff data interview candidates rarely have first-hand." Slot order: P10 → P11 → P13 → **P14** → P12.
- **P12 (expanded v8): 5-framework agent showdown** — AutoGen + LangGraph + CrewAI + Claude Agent SDK + OpenAI Agents SDK. Build the same simple task agent (research a topic, return a sourced summary) in all 5. Measure: LoC, latency, cost per task, debuggability, dev ergonomics. End artifact: comparison table + LinkedIn-ready technical blog ranking the frameworks for different use cases.

## P7 → MatchScout Pivot (2026-05-09)

P7 was originally "ChurnGuard" — a synthetic SaaS churn prediction agent.
Pivoted to **MatchScout** — a real Onemyle initiative with the same learning
objectives but framed as a formal pro bono PoC at Onemyle (where Rajesh is
an angel investor + pro bono Product/AI Lead).

**Why pivot:** ChurnGuard would have been a hobby project on the resume.
MatchScout is a formal Onemyle initiative — credible, real, defensible in
interviews. Same technical learning + marketplace AI patterns added.

**MatchScout = gig-driven AI recommender for Onemyle's two-sided marketplace** (creators ↔ local businesses). When a business posts a gig and clicks "Recommend Creators" (PoC: `python recommend_creators.py --gig-id GIG_ID`), the system surfaces the top 3 creators. 10% of gigs go through a no-LLM control path; 90% go through an LLM re-ranker that reasons over each candidate's past-gig metrics. Outcome A/B measures whether the LLM beats the baseline.

**Status:** PoC. Synthetic data. Productionization pending Onemyle roadmap.

**Replaces:** P7 #40, #41, #42, #79 (those tickets superseded). PM artifact ticket (was #81) is incorporated into MatchScout deliverables.

**Ticket:** #87 — MatchScout — Onemyle Marketplace PoC.

**Repository:** https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout (split out of this repo on 2026-06-08; local clone at `~/ai/Onemyle-matchscout/`)
**Design doc:** [DESIGN.html](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout/blob/main/DESIGN.html) (architecture, data flow, two-arm outcome eval)
**Operating doc:** [project_workflow.html](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout/blob/main/project_workflow.html) (phase-by-phase plan + remediation appendix)
**Interview pitch:** [pm/interview_pitch.md](https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout/blob/main/pm/interview_pitch.md) (cheat sheet for live interviews)

### P7 design summary

- **Entities:** Creator + Business (CSV catalog) · Gig + CreatorRecommendation + PastGig (SQLite)
- **Stages:** Stage 1 hard filter (location · budget · content_type) → Stage 2 vector cosine on (niche_tags + profile_description + categories + subcategories) → Stage 3 arm-routed: Arm 1 (10% control) takes top 3 by cosine; Arm 2 (90%) LLM picks top 3 from top 10 using past-gig metrics + versioned prompt template
- **Prompt as tuning surface:** versioned template files (`prompts/arm2_v1.txt`, ...). `prompt_version` stamped on every recommendation. Outcome dashboard segments metrics by prompt version. Iteration is empirically driven.
- **Storage:** SQLite for gigs/recommendations/past_gigs (joinable, queryable, VS Code SQLite Viewer for inspection). CSVs for immutable catalog.
- **Dashboard:** Streamlit, two-arm side-by-side with chi-squared significance, drill-down to LangSmith traces.
- **Eval:** outcome-based only. NO synthetic golden set. NO CI quality gate. CI = pytest schema smoke test only. Ragas/DeepEval/Promptfoo are dev-time tools used during prompt iteration, not blockers.

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

## Current Status (as of 2026-06-23)

### Curriculum build phase — COMPLETE for P1–P7
- [x] P1 ToolBot — COMPLETE (quiz 7/7)
- [x] P2 DocTalk — COMPLETE (quiz 6.5/8)
- [x] P3 ResearchBot — COMPLETE (quiz 6.5/7)
- [x] P4 StockSage — COMPLETE (quiz 6.5/8)
- [x] P5 ReviewCrew — COMPLETE (quiz 6/6)
- [x] P6 MCP++ — COMPLETE (quiz 5/7)
- [x] P7 MatchScout — **substantively COMPLETE** for job-application purposes (Phases 0–5 done, LangSmith @traceable shipped, Phases 5.4/5.5 + 6–8 deferred indefinitely)
- [x] HPRC Framework — built offline 2026-05-31 to 2026-06-03 at ~/ai/Prep, Apache-2.0 open source (NOT a curriculum project — added as a portfolio centerpiece)

### Build phase — DEFERRED post-job-search (mostly)
- P8 PII Compliance · P9 standalone 4-framework memory benchmark (rolled into P13) · P10 AgentPlatform · P11 Multimodal · P12 5-framework showdown · P14 MatchScout V3 Managed Agents

### Build phase — MOVED UP 2026-06-25, expanded 2026-06-26
- **P13 MatchScout V2 — Agent SDK rebuild on AWS Bedrock** — pulled out of deferred. Slots after the P2 Pinecone variant. Driver: Claude Agent SDK + subagents + Anthropic Memory tool + Reflexion + **AWS Bedrock** show up across active JDs and want portfolio coverage now. Carries `advanced_patterns/03_reflexion/` along since the critic subagent IS Reflexion.
- **Bedrock fold-in (2026-06-26):** P13 will use Bedrock-hosted Claude Sonnet 4.6 via `boto3` + Claude Agent SDK rather than direct Anthropic API. Real enterprise scenario (IAM, billing, compliance, VPC). Captures: IAM role + Bedrock model access, cross-region inference profiles, Bedrock Guardrails, CloudWatch Logs traces, Bedrock vs direct-API cost comparison.
- **Optional Bedrock primer (pending user decision):** standalone ~100-line `bedrock_primer.py` slotted between Pinecone and P13 for AWS console familiarity. User to confirm yes/no on next session.

### Active phase — REVISION ARC + JOB SEARCH (since 2026-05-27)
**P1–P7 deep-walk revision for interview prep** is in flight, interleaved with job-application pipeline.
- [x] P1 ToolBot revision — COMPLETE (6 concepts)
- [x] P2 DocTalk revision — COMPLETE (5 concepts)
- [x] **P3 ResearchBot revision — COMPLETE 2026-06-25** (all 8 concepts; Concept 8 Kafka quiz 5/8 with gap-fills patched into Appendix J of master guide)
- [ ] **P5 ReviewCrew revision — IN PROGRESS** (kicked off 2026-07-01; consolidation of all 3 CrewAI orchestration modes into `p5_reviewcrew/` complete; awaiting Phase A on Concept 1)
- [ ] P6 MCP++ revision — queued
- [ ] P7 MatchScout revision — queued

**Active queue order (re-locked 2026-06-26; P2 + P2.5 closed 2026-06-29 → 2026-07-01):**
1. P2 Pinecone variant (`p2_doctalk/doctalk_pinecone.py`) — ✅ DONE (289 chunks, side-by-side vs Qdrant, real numbers in Appendix K §9.5)
2. P2.5 AWS Bedrock primer (`p2_5_bedrock_primer/bedrock_primer.py`) — ✅ DONE 2026-07-01 (Bedrock 12.2s @ $0.00126 vs Direct Anthropic 15.2s @ $0.00127, real case study in Appendix L §10.5; cross-region model ID required for Claude Sonnet 4.6+)
3. **P5 ReviewCrew revision — IN PROGRESS (started 2026-07-01)** — 5 concepts locked, `crew_hierarchical.py` added to consolidate all 3 modes side-by-side
4. P6 MCP++ revision
5. **P13 MatchScout V2 Agent SDK rebuild on Bedrock** (carries `advanced_patterns/03_reflexion/`; Bedrock-hosted Claude via boto3 + Agent SDK)
6. Database Foundations + Phase-A quizzes (PostgreSQL + MongoDB)
7. Task 2 — System design 15 prioritized patterns
8. Remaining advanced patterns (`advanced_patterns/04`–`27` placeholders ready)
9. P7 MatchScout revision (saved as closer — most-fluent project, warm-up before interviews)

**SKIPPED:** P4 StockSage revision (user call 2026-06-25 — already comfortable with multi-tool orchestration concepts).

**Per-concept workflow (updated 2026-06-22):** code re-read → **Phase A: 6-10 objective-type questions** (MCQ/T-F/fill-in-blank/match — NOT free text) → grade + gap-fill → Phase B (2–3 sharpest interview-grade points) → patch INTERVIEW_STUDY_GUIDE.html and cheatsheets. See `feedback_phase_a_objective_format.md`.

### Interview prep tasks (interleaved with revision arc — see plan.txt)
- [x] Task 1 — Claude Code interview Q&A — patched into study guide 2026-06-18
- [x] **Task 3 — Common agentic AI interview Q&A bank — COMPLETE 2026-06-23**. 150 questions across 13 categories at `advanced_patterns/interview_questions_bank.html`, also Appendix E of the master guide.
- [ ] Task 2 — System design prioritized ~15 patterns — queued (after P4)
- [ ] **Database Foundations (PostgreSQL + MongoDB short courses)** — added to plan.txt 2026-06-23, not yet started; suggested slot between P4 and Task 2.

### Active job applications (as of 2026-06-26 — 8 in flight)
| Company | Role | Track | Applied |
|---|---|---|---|
| Apple | Agentic AI Product Manager (Austin) | AI PM | 2026-06-11 |
| Oracle OCI | Sr. Principal TPM (DC Expansion SWAT) | DC Infra PM | 2026-06-12 |
| Palo Alto Networks | 10x AI Engineer | AI Engineer | 2026-06-17 |
| Heartflow | Senior Agentic AI Engineer | AI Engineer | 2026-06-17 |
| NVIDIA | Senior TPM, Server Engineering Operations | DC Infra PM | 2026-06-18 |
| **Apple ASE PMO** | Program Manager, PMO (Apple Services Engineering) | PM + AI fluency | **2026-06-22 — strongest fit** |
| Cerebras Systems | Sr TPM, AI Infrastructure / Site Operations | DC Infra PM | 2026-06-24 (resume built; user confirmed apply) |
| **Oracle** | **Sr Principal TPM (IC5, Cloud Transformation + AI/Automation)** | **DC Infra / Cloud Transformation** | **2026-06-26 ✅ applied** |

**Skipped in this batch (2026-06-26):** Particle41 AI Engineer — explicit user call, JD wanted broad ML (TensorFlow/PyTorch/fine-tuning/TTS/STT/computer vision/time-series/MLflow), Rajesh's stack is agentic-orchestration depth not ML breadth, ~40% real coverage. Resume built (`RESUME_PARTICLE41_AI_ENGINEER.{md,docx,pdf}`) but not submitted. Files on disk for reference.

**Earlier skipped:** NVIDIA Agentic Engineering (compiler/GPU specialized) · Equinix Senior Staff (deferred).

### Agentic AI deep-dive — depth-not-breadth strategy (set 2026-06-26)
The "limitless info" trap. The 2026 market is converging around a smaller must-know set. Pick 3-5 areas of credible depth; let the rest be defensible breadth.
- **Tier 1 — build into real code (interview-leverage maximum):** Claude Agent SDK · AWS Bedrock · Reflexion / self-critique · Subagent decomposition with fact-checker · Cost / latency observability at scale. All landing in P13.
- **Tier 2 — read deeply enough for strong opinion:** OpenAI Agents SDK · AutoGen v0.4+ · LangGraph Send API + advanced patterns · LLM-as-judge biases + multi-family judge ensembles · Constitutional AI.
- **Tier 3 — defensibly aware, don't drill:** Fine-tuning (defensible as "prompt engineering + structured output gets us 95%") · Computer vision agents · Voice agents (LiveKit/Deepgram) · RLHF · Niche frameworks (Pydantic-AI, Phidata, Letta).

**Standing rule when a recruiter responds:** drop revision/curriculum work, load the corresponding interview-prep memory file, start mocking.

### Advanced Patterns track (parallel to main curriculum)
- [x] A1 Orchestrator-Worker — README + runnable `pattern.py` at `advanced_patterns/01_orchestrator_worker/`
- [x] Supervisor (CrewAI Process.hierarchical) — README + runnable `pattern.py` at `advanced_patterns/02_supervisor_crewai/`
- [ ] Remaining 20 patterns from the curated 22-pattern advanced track (queued in `advanced_patterns/README.md`)

### Master Guide (consolidated doc — built 2026-06-23)
`AGENTIC_AI_MASTER_GUIDE.html` at repo root: 851KB consolidated document with 6 navigable sections (cheatsheet + study guide + 5 appendices). Gitignored — it's a derived artifact built from source files via `/tmp/build_master_guide.py`. See `project_master_guide.md` memory file for build details.

## Resume + Cover Letter Pipeline
- Markdown source: `RESUME_*.md` / `COVER_LETTER_*.md` at repo root
- Build pipeline: `pandoc → docx → _compress_resume.py` (margin/font/spacing compression)
- Optional PDF: `_build_resume_pdf.sh` (pandoc → standalone HTML → Chrome headless)
- Locked profile summary for active batch: stored in `~/.claude/projects/.../memory/project_resume_summary_batch_2026_06.md`
- Style rules (set 2026-06-15): no em-dashes in cover letters; no "12+ years" specific count; no PATENT section; no expired NVIDIA AI-in-the-Data-Center cert
- Don't-oversell calibration: MatchScout labeled "PoC" honestly; HPRC labeled "open-source framework" not "production at scale"

## Repository Architecture (post-split 2026-06-08)
- **`ai_engineer_program`** (this repo) — curriculum projects P1–P14 + interview study guide + cheatsheets + resume pipeline
- **`Onemyle-matchscout`** (separate repo, ~/ai/Onemyle-matchscout/) — MatchScout PoC, split out 2026-06-08
- **HPRC Framework** (~/ai/Prep/) — open-source, lives under its own GitHub org `HPRCFramework` (separate from `Agentic-and-AI-Engineering-Projects`)

## Related Projects
- Onemyle / reel-analysis-lib: ~/ai/Onemyle/reel-analysis-lib (real-world agent deployment)
- MyKanban: ~/ai/mykanban (the Kanban tool used to track this program)
- Onemyle MCP server: related to P6 MCP++ project
