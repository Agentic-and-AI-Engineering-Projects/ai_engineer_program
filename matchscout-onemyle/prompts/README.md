# MatchScout Prompts

This folder holds versioned prompt templates for the Arm 2 LLM ranker. The prompt is the **primary tuning surface** for the LLM stage — outcome metrics drive prompt iteration; each iteration is a new file in this folder.

## How it works

- `agent.py` reads `PROMPT_VERSION` from env (default: `arm2_v1`)
- Loads `prompts/{PROMPT_VERSION}.txt` and `.format()`s in the runtime data
- Each recommendation row stamps the `prompt_version` it used
- The outcome dashboard groups metrics by `(treatment_arm, prompt_version)` so you can causally compare prompt versions on real outcomes

## Iteration loop

```
1. Deploy current prompt → measure on real gigs over N days
2. Dashboard shows a weakness (e.g. acceptance plateaus, top-1 rate low)
3. Read 5-10 LangSmith traces to form a hypothesis
4. Edit the prompt → save as a new version file (e.g. arm2_v2.txt)
5. Update PROMPT_VERSION env → deploy
6. Measure → compare segmented metrics in dashboard
7. v2 wins? Lock in. v2 loses? Roll back. Log the experiment below.
```

## Version log

### `arm2_v1.txt` — initial prompt (2026-05-12)

The starting prompt. Holistic ranking over 4 signals (successful gigs, failed gigs, follower count, ratings) with explicit guidance that no single metric dominates. Forbids vanity-metric-only reasoning. Asks for strengths, risks, reliability estimate, campaign value per creator, then top 3 selection with reasoning.

**Placeholders:**
- `{gig_brief}` — formatted gig details (location, budget, content needs, niche tags)
- `{candidates_table}` — 10-row table of per-creator metrics + per-metric ranks
- `{candidates_recent_gigs}` — recent gig history per candidate
- `{output_schema}` — JSON schema for the expected output structure

**Status:** baseline. No outcome data yet.

---

(Add new entries above this line as new prompt versions ship.)
