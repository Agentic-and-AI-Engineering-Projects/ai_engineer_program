# 16 — Layered Guardrails (Input / Output / Tool)

**Status:** placeholder · queued.

## What this pattern is

Pre-call + post-call + tool-permission scope; Llama Guard 3 + custom.

Three orthogonal layers: validate input before the LLM sees it, validate output before it goes to the user, scope tool permissions to what the agent should be able to do. Each layer catches different failure modes.

## Why this folder is a placeholder

This pattern is queued in the advanced patterns track (see `../README.md` for full curriculum). To be built as a standalone runnable example with:

- `pattern.py` — runnable end-to-end with synthetic data
- README expansion: architecture diagram, when-yes / when-no, anti-patterns, real-world examples
- `example_output.txt` — captured output from a real run

Slot in when the interview-prep / job-search queue opens up.
