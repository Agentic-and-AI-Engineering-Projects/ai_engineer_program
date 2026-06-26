# 23 — Multi-Family Judge Ensemble

**Status:** placeholder · queued.

## What this pattern is

Cross-family LLM judges mitigate self-preference + preference-leakage.

ICLR 2026 result: LLM-judges have ~28.7% self-preference bias. Running an ensemble across Claude + GPT-4 + Gemini and taking a majority vote materially reduces this.

## Why this folder is a placeholder

This pattern is queued in the advanced patterns track (see `../README.md` for full curriculum). To be built as a standalone runnable example with:

- `pattern.py` — runnable end-to-end with synthetic data
- README expansion: architecture diagram, when-yes / when-no, anti-patterns, real-world examples
- `example_output.txt` — captured output from a real run

Slot in when the interview-prep / job-search queue opens up.
