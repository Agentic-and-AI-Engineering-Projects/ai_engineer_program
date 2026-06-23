# A1 — Orchestrator-Worker Pattern

The ~70% production case for multi-agent systems (per 2026 Anthropic / OpenAI / Stripe / Mercury reference designs). Same DIAGRAM shape as hub-and-spoke; very different behavior at the LLM-call layer.

## The pattern

```
                  ┌──────────────────┐
                  │   Orchestrator   │   ← LLM decomposes task
                  │   (Claude)       │      into N subtasks DYNAMICALLY
                  └────────┬─────────┘      (number known only at runtime)
                           │
                           │  Send API dispatches
                           │  one worker per subtask
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌──────────┐       ┌──────────┐       ┌──────────┐
  │ Worker 1 │       │ Worker 2 │  ...  │ Worker N │   ← parallel,
  │ (Q: ...)  │       │ (Q: ...)  │       │ (Q: ...)  │      task-specific
  └─────┬────┘       └─────┬────┘       └─────┬────┘      input
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  ┌──────────────────┐
                  │   Synthesizer    │   ← LLM synthesizes all worker
                  │   (Claude)       │      outputs into coherent answer
                  └──────────────────┘
```

## How it differs from Hub-and-Spoke (Concept 7)

| Property | Hub-and-Spoke | Orchestrator-Worker |
|---|---|---|
| Central node | No-op dispatcher (returns `{}`) | LLM call — decomposes task |
| Spoke count | Fixed at design time (3 in hub_spoke.py) | Decided at runtime by the orchestrator |
| Spoke input | All get the same state | Each gets a task-specific payload via Send API |
| Synthesis | Separate aggregator node that just concatenates | LLM call that produces coherent narrative |
| Cost | Predictable (N hardcoded × LLM) | Variable (LLM plans + N workers + LLM synthesizes) |

## When to pick it

Pick orchestrator-worker when:
- The work decomposition itself requires reasoning (cannot be pre-specified)
- Different inputs need different workers / different prompts per worker
- Synthesis quality matters more than synthesis cost
- Examples: deep research agents, code-modification agents, plan-and-execute systems

Pick hub-and-spoke when:
- The specialist set is fixed and known at design time
- All spokes do equivalent work on the same input
- Examples: multi-source aggregation, classifier ensembles, fixed content-moderation flows

## Implementation notes

This implementation uses LangGraph's **Send API** for dynamic fan-out. The dispatch function returns a list of `Send("worker", payload)` instances — LangGraph spawns one parallel worker invocation per Send. Each worker receives its own state (the payload), not the global state. Worker outputs are merged back into the global state via the reducer on `findings`.

## Files

- `pattern.py` — runnable end-to-end example: research a topic with dynamic question decomposition
- `example_output.txt` — captured output from a real run

## Running it

```bash
# From repo root with .venv activated
python advanced_patterns/01_orchestrator_worker/pattern.py "quantum computing"

# Or with default topic
python advanced_patterns/01_orchestrator_worker/pattern.py
```

Requires: `ANTHROPIC_API_KEY` in `.env`. Costs ~$0.01 per run (1 Claude call for orchestrator + N for workers via Claude OR free via DuckDuckGo + 1 Claude call for synthesis).

## Production extensions (not in this demo)

- Per-worker timeout (slow worker shouldn't block synthesis)
- Required vs optional workers (one failing shouldn't kill the run)
- Worker output schema validation (Pydantic + retry on malformed output)
- Cost cap (max workers × max tokens per worker)
- Provenance tagging (which worker produced each finding)
- Persistent checkpointing for resumable long-running orchestrations
