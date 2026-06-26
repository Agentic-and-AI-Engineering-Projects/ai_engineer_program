# 19 — Bounded Retry with Drift Detection

**Status:** placeholder · queued.

## What this pattern is

Retry N times on structured-output failure + drift tracking.

Cap retries to prevent infinite loops; track per-prompt-version retry rates to catch silent quality drift before it ships.

## Why this folder is a placeholder

This pattern is queued in the advanced patterns track (see `../README.md` for full curriculum). To be built as a standalone runnable example with:

- `pattern.py` — runnable end-to-end with synthetic data
- README expansion: architecture diagram, when-yes / when-no, anti-patterns, real-world examples
- `example_output.txt` — captured output from a real run

Slot in when the interview-prep / job-search queue opens up.
