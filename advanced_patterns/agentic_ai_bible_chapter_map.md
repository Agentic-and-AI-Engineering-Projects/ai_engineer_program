# Agentic AI Bible — Chapter ↔ Pattern Map

The companion code repo ([trcaldwell/agentic-ai-bible](https://github.com/trcaldwell/agentic-ai-bible)) is cloned at `advanced_patterns/agentic-ai-bible/` (gitignored). Each book chapter maps to one or more existing pattern placeholders below — the bible's code provides reference reading; the `chapterNN.html` files in `advanced_patterns/` provide our own written explanation (in lieu of the paperback text).

| Bible Ch | Title | Maps to existing patterns |
|---|---|---|
| 3 | The Agent Loop | foundational — see [INTERVIEW_STUDY_GUIDE.html] Concept 1, P1 ToolBot |
| 5 | LLMs as Reasoning Engines | foundational — see P1 ToolBot Concept 3 |
| 6 | Tool Use and Function Calling | foundational — see P1 ToolBot Concept 4 |
| 7 | Memory | `11_distilled_facts_memory/`, `12_working_set_archival_letta/`, `13_temporal_knowledge_graph_zep/`, `14_dreaming_memory_consolidation/`, `15_reflexion_memory/` |
| 8 | Planning and Decomposition | `04_planner_generator_evaluator/`, `09_adaptive_planning/` |
| 9 | Model Context Protocol (MCP) | curriculum P6 MCP++ |
| 10 | Single-Agent Patterns | scratchpad / step-machine / validation patterns (foundational) |
| 11 | Multi-Agent Systems | `01_orchestrator_worker/` ✅, `02_supervisor_crewai/` ✅, `06_fan_out_fan_in_send_api/`, `07_multi_agent_debate/`, `08_dynamic_handoff/` |
| 12 | Human-in-the-Loop | `21_human_in_loop_approval/` |
| 13 | Long-Running Agents | durability / checkpoint / idempotency-key patterns |
| 14 | Observability and Evaluation | `22_two_arm_outcome_ab/`, `23_multi_family_judge_ensemble/` |
| 15 | Safety and Guardrails | `16_layered_guardrails/`, `18_refusal_as_tool/`, `24_constitutional_validation/` |
| 16 | Security | prompt injection detection (new territory) |
| 17 | Cost and Performance | `26_token_budget_compaction/`, `27_model_routing_by_complexity/` |
| 18 | Deployment and SRE | `25_per_tenant_rail_configs/`, canary patterns |
| 19 | Computer-Use Agents | new territory |
| 20 | Coding Agents | new territory |
| 21 | Case Studies | not patterns — real-world systems |

## Convention

Each bible chapter gets a `chapterNN.html` at `advanced_patterns/chapterNN.html` (NOT inside a pattern folder, since most chapters span multiple patterns). The HTML provides:

- The chapter's topic / what it teaches
- Walk-through of the chapter's code samples (one section per file in `chapters/chNN/`)
- Cross-references to the existing pattern folders this chapter overlaps with
- "If you ONLY have time for one example" callout
- Interview-grade takeaways

## Why this format

The user owns the paperback — these HTMLs are NOT a replacement for the book. They serve as:

1. **Index** — quickly locate which bible chapter covers a given concept
2. **Code commentary** — what each `chNN_NN_*.py` file demonstrates, in our voice
3. **Bridge** — connect the bible's organization to our advanced-patterns folder structure
4. **Self-contained when needed** — for sessions when the paperback isn't at hand
