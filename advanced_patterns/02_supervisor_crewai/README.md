# Supervisor Pattern (CrewAI Process.hierarchical)

The full-LLM-delegation orchestration pattern. A manager agent decides which specialist runs, in what order, and may loop back for revisions — all dynamically. Same problem as A1 Orchestrator-Worker, but the LLM controls more of the execution graph.

## The pattern

```
                  ┌──────────────────┐
                  │ Manager Agent    │   ← LLM decides:
                  │ (LLM-driven)     │     - which specialist next
                  └────┬─┬─┬─────────┘     - when to revise
                       │ │ │               - when to stop
        ┌──────────────┘ │ └──────────────┐
        ▼                ▼                ▼
  ┌──────────┐    ┌──────────┐     ┌──────────┐
  │Researcher│    │  Writer  │     │  Editor  │   ← specialists with
  │  agent   │    │  agent   │     │  agent   │      different skills
  └─────┬────┘    └─────┬────┘     └─────┬────┘
        │               │                 │
        └───────────────┴─────────────────┘
                        │ output flows back to manager
                        ▼
              ┌──────────────────┐
              │ Manager LLM      │   ← decides next move or done
              └─────────┬────────┘
                        ▼
                 (loop until done)
```

Every arrow flows back to the manager — the manager keeps control after each specialist returns, deciding the next move.

## How this differs from A1 Orchestrator-Worker

Same use case (research a topic). Very different execution shape.

| Property | A1 Orchestrator-Worker (LangGraph) | This — Supervisor (CrewAI hierarchical) |
|---|---|---|
| Central decision | One LLM call: "decompose into N questions" | Many LLM calls: "what next?" after every specialist returns |
| Specialist set | Single worker type, N parallel instances | Multiple distinct specialists (researcher, writer, editor) |
| Dispatch shape | Parallel fan-out via Send API | Serial delegation, manager picks one at a time |
| Number of LLM calls per run | Predictable: 2 + N (orchestrator + N workers + synthesizer) | Variable: M delegations × (manager + specialist) calls |
| Synthesis | Separate synthesizer LLM node | Manager itself synthesizes (no separate node) |
| Code abstraction | Lower — explicit graph wiring | Higher — declarative agent definitions |
| Best for | Independent decomposition, parallel work | Specialist-rich workflows with iterative refinement |

## When to pick Supervisor over Orchestrator-Worker

Pick Supervisor when:
- You have a SET of specialists with DIFFERENT skills (researcher, writer, editor are not interchangeable)
- The flow between specialists is unpredictable — manager needs to look at intermediate output before deciding next move
- Revisions and looping are part of the workflow (writer drafts → editor reviews → writer revises)
- You value declarative role definitions over explicit graph control

Pick Orchestrator-Worker when:
- Workers are interchangeable (single worker type, N parallel instances)
- Each subtask is independent
- You need predictable cost (N is decided once)
- You want fine-grained observability into every LLM call

## Production tradeoffs

| Concern | Detail |
|---|---|
| **Cost variability** | Manager makes a decision after every specialist call. M delegations × 2 LLM calls (manager + specialist) = unbounded cost. Always pair with iteration cap. |
| **Manager runaway** | A buggy manager may loop indefinitely. Set `max_iter` on the Crew or count delegations manually. |
| **Specialist coupling** | If manager decisions depend on full conversation history, specialists are effectively coupled through the manager's context. Plan for context bloat. |
| **Observability** | Harder to trace than orchestrator-worker because the manager's reasoning is the orchestration layer. CrewAI's verbose mode helps; LangSmith integration available. |
| **Determinism** | Lower than orchestrator-worker. Same input may produce different delegation sequences across runs. |

## Files

- `pattern.py` — runnable end-to-end example using CrewAI Process.hierarchical
- `example_output.txt` — captured output (after first run)

## Dependencies

P5 already installed CrewAI. If running fresh:

```bash
pip install crewai crewai-tools
```

Requires `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) in `.env`. Costs ~$0.05-0.15 per run depending on how much the manager delegates.

## Running it

```bash
python advanced_patterns/02_supervisor_crewai/pattern.py "quantum computing"
```

The output will show the manager's delegation decisions inline — watch for `[DEBUG]: Working Agent: ...` lines showing which specialist is active at each step.

## Compare with the curriculum

This pattern is **not** what P5 ReviewCrew uses. P5 uses `Process.sequential` — tasks run in a fixed order. This is the hierarchical alternative. The shape difference:

| | P5 ReviewCrew (sequential) | This (hierarchical) |
|---|---|---|
| Process | `Process.sequential` | `Process.hierarchical` |
| Manager | None — task order is hardcoded | Manager agent decides dynamically |
| Tasks | Run in declared order | Manager picks task assignment |
| Cost | Predictable: one call per task | Variable: manager calls between tasks |
| Best for | Known fixed pipeline | Adaptive multi-specialist workflows |
