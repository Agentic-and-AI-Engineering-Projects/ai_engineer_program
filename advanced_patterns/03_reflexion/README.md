# 03 — Reflexion / Self-Critique Pattern

**Status:** placeholder · queued for build after P2 Pinecone variant.

## What this pattern is

Reflexion is a loop where an LLM critiques its own output against a rubric and revises until the critic approves (or a max-iteration cap fires). Distinct from simple "verify-then-emit" because the **self-critique becomes durable memory** — failed reasoning patterns get logged as anti-patterns the agent steers away from on future runs.

Two roles, one loop:

1. **Generator** — produces a candidate answer
2. **Reflector** — scores the candidate against a rubric, emits structured critique
3. **Generator (revise)** — incorporates the critique, produces v2
4. **Loop** until reflector approves or `max_iter` hit

Optional 4th: **Reflexion memory** — store rejected critiques as "things to avoid" that get injected into future generator prompts.

## Why this folder is a placeholder

This pattern is item 6 in the post-Pinecone roadmap. Slated as a standalone ~150-line build:

- `pattern.py` — runnable end-to-end with synthetic data
- README expanded with diagram, when-yes / when-no, anti-patterns, comparison with Fact-Checker Subagent (C2)
- `example_output.txt` — captured generator-reflector-generator transcript

## Where this pattern shows up in the curriculum

- **P13 (deferred)** — MatchScout V2 Agent SDK rebuild has a critic subagent that uses Reflexion to write self-critiques into reflexion memory.
- **P9 (deferred)** — Reflexion memory is one of the 5 memory types in the 4-framework benchmark.
- **Advanced patterns track #68** — listed as supplementary in CLAUDE.md.

Building this folder first means the pattern is ready as soon as P13 / P9 come up.

## When to use vs not (preliminary — to be expanded)

**Use Reflexion when:**
- High-stakes output (legal, medical, financial advice) where one bad answer is costly
- Output has objectively-checkable structure (citations to verify, code that must compile, JSON that must validate)
- You're tuning prompts iteratively and want the critique stream as a debugging signal

**Don't use Reflexion when:**
- Casual chat — the cost-to-value ratio doesn't pencil
- The critic has no signal beyond "looks good to me" — without a real rubric this collapses to two LLMs agreeing with each other
- Hard latency budgets — Reflexion doubles or triples per-call latency
