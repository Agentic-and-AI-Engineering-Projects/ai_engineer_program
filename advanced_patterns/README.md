# Advanced Agentic Design Patterns (separate track)

Production patterns used in enterprise agentic AI pipelines as of mid-2026. Curated from Anthropic + OpenAI reference designs, production case studies (Stripe, Mercury, Ultra Code), and emerging Q1–Q2 2026 patterns surfaced via WebSearch.

## Format per pattern

Each pattern lives in its own subfolder with:

1. **`README.md`** — design doc: problem the pattern solves, architecture diagram, when to use vs not, real-world examples, anti-patterns
2. **Runnable code** — `pattern.py` (and supporting files) that runs end-to-end with synthetic data
3. **`example_output.txt`** — captured output from a real run

Workflow: Claude writes the design + code, Rajesh reads and reviews, asks questions, follows up. No exercises — this is reference material.

## Curriculum order (sequenced)

Suggested order is: orchestration core → memory → safety → eval → cost → remaining frontier.

### A. Orchestration Patterns

- [x] **A1 — Orchestrator-Worker** (M) — single planner decomposes task, dispatches workers, synthesizes. ~70% of production multi-agent setups. ✅ 2026-06-23 — see `01_orchestrator_worker/`
- [ ] **A2 — Planner-Generator-Evaluator** ⭐ NEW (M) — three roles with structured-artifact handoff instead of shared context (Anthropic Q1 2026 pattern).
- [ ] **A3 — Sequential Pipeline** (S) — fixed linear steps, each depends on prior output.
- [ ] **A4 — Fan-out / Fan-in with Send API** (M) — parallel workers + reducer-merged aggregator.
- [ ] **A5 — Multi-Agent Debate** (M) — two+ agents argue, third synthesizes/decides; maker-checker loops.
- [ ] **A6 — Dynamic Handoff** (L) — agent decides which specialist to route to mid-conversation.
- [x] **Supervisor (CrewAI Process.hierarchical)** ✅ 2026-06-23 — see `02_supervisor_crewai/`. Manager agent + 3 specialists (researcher/writer/editor). Same research-topic use case as A1 for direct compare/contrast.
- [ ] **A7 — Adaptive Planning (Open-Ended)** (L) — planning itself is discovered, not fixed.
- [ ] **A8 — Tournament Pattern** ⭐ NEW (L) — spawn N candidates, pairwise compare, keep winner (Ultra Code).

### B. Memory & State Patterns

- [ ] **B1 — Distilled Facts Memory** (M) — atomic claim extraction + retrieval (Mem0-style).
- [ ] **B2 — Working Set + Archival (Letta)** (L) — OS-style virtual context, page in on demand.
- [ ] **B3 — Temporal Knowledge Graph (Zep)** (L) — time-aware facts with versioning.
- [ ] **B4 — Dreaming / Memory Consolidation** ⭐ NEW (L) — scheduled offline session review + pattern distillation.
- [ ] **B5 — Reflexion Memory** (M) — self-critiques as anti-pattern guardrails.

### C. Reliability & Safety Patterns

- [ ] **C1 — Layered Guardrails (Input/Output/Tool)** (M) — pre-call + post-call + tool-permission scope; Llama Guard 3 + custom.
- [ ] **C2 — Fact-Checker Subagent** (M) — inline subagent validates citations against source-of-truth before emit.
- [ ] **C3 — Refusal-as-Tool** (S) — explicit refusal as typed return shape.
- [ ] **C4 — Bounded Retry with Drift Detection** (M) — retry N times on structured-output failure + drift tracking.
- [ ] **C5 — Governance Agents Monitoring Agents** ⭐ NEW (L) — meta-layer policy/bias/drift detection.
- [ ] **C6 — Human-in-the-Loop Approval Queue** (M) — risky decisions pause for human + audit trail.

### D. Evaluation & Feedback Patterns

- [ ] **D1 — Two-Arm Outcome A/B** (M) — holdout control vs treatment, real-world outcomes; MatchScout pattern.
- [ ] **D2 — Multi-Family Judge Ensemble** (M) — cross-family LLM judges mitigate self-preference + preference-leakage (28.7% bias, ICLR 2026).
- [ ] **D3 — Constitutional Validation** (M) — output checked against declared principles before emission.

### E. Cost & Performance Patterns

- [ ] **E1 — Per-Tenant Rail Configs** ⭐ NEW (L) — different guardrail/cost/permission policies per customer (gateway pattern).
- [ ] **E2 — Token Budget + Compaction** (S) — per-request token cap + older-context summarization.
- [ ] **E3 — Model Routing by Complexity** (M) — cheap model for triage, expensive for hard cases; ~60% cost reduction in production.

## Relationship to the main curriculum

These patterns are a **separate, parallel track** from the project curriculum (P1–P14). They are reference designs, not exercises. The main curriculum's revision arc (P1–P7 deep walks) and job-search work take priority; these patterns get covered during sessions Rajesh dedicates to advanced-pattern review.

## Source links (June 2026 research)

- Multi-agent orchestration patterns: https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production
- Multi-LLM orchestration battle-tested patterns: https://www.velsof.com/ai-automation/multi-llm-orchestration-patterns/
- Claude Agent SDK Q2 2026 architecture (Zylos Research): https://zylos.ai/research/2026-04-20-claude-agent-sdk-managed-agents-architecture/
- Code with Claude 2026 — 5 new agent features: https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features
- LLM Guardrails 2026: https://futureagi.com/blog/ultimate-guide-llm-guardrails-2026/
- LLM Safety production patterns: https://pdpspectra.com/blog/llm-safety-guardrails-2026/
- Agentic AI Design Patterns 2026: https://blckalpaca.at/en/blog/agentic-ai-design-patterns-for-2026-build-trustworthy-systems
- Enterprise Agentic AI Architecture: https://www.kellton.com/kellton-tech-blog/enterprise-agentic-ai-architecture
