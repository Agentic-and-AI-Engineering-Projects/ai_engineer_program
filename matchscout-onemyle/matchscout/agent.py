"""
Stage 3 of the MatchScout pipeline — the LLM re-ranker.

Takes the top-10 ranked candidates from Stage 2 and produces the final 3
CreatorRecommendations, via one of two arms:
  - no_llm : top 3 by cosine score, no reasoning
  - llm    : Claude ranks the top 3 with reasoning over past-gig metrics

This file is built in sub-steps:
  2.3a (this) — compute per-candidate metrics from past gigs
  2.3b        — format the prompt
  2.3c        — call Claude, parse the response
  2.3d        — LangGraph wiring + arms + public entry point
"""

from dataclasses import dataclass, field

from matchscout.schemas import Gig, Creator
from matchscout import db



# ============================================================
# 2.3a — per-candidate metrics
# ============================================================

@dataclass
class CandidateMetrics:
    """A Stage-2 candidate plus the historical metrics Arm 2's LLM reasons over.

    Transient — built per pipeline run, never stored. Ranks are filled in
    after every candidate's raw metrics are computed.
    """
    creator: Creator
    cosine_score: float           # similarity score from Stage 2
    successful_gigs: int
    failed_gigs: int
    total_gigs: int               # successful + failed
    success_pct: float            # successful / total (0.0 if no past gigs)
    failure_pct: float            # failed / total     (0.0 if no past gigs)
    follower_count: int
    avg_rating: float | None      # None if the creator has no rated past gigs
    recent_gigs: list[Gig]        # raw past gigs — used later for prompt context

    # competition rank within the set on each metric; N = best, ties shared
    success_rank: int = 0
    failure_rank: int = 0
    follower_rank: int = 0
    ratings_rank: int = 0


def _competition_rank(metrics, value_of, higher_is_better=True) -> dict[str, int]:
    """Competition ranking:  rank = N - (count of candidates strictly better).

    The best candidate gets N; tied candidates share a rank; a gap follows
    a tie (e.g. ranks 10, 9, 9, 7 — never a 8 after two 9s).
    Returns {creator_id: rank}.
    """
    n = len(metrics)
    ranks = {}
    for m in metrics:
        mine = value_of(m)
        if higher_is_better:
            strictly_better = sum(1 for other in metrics if value_of(other) > mine)
        else:
            strictly_better = sum(1 for other in metrics if value_of(other) < mine)
        ranks[m.creator.id] = n - strictly_better
    return ranks


def _assign_ranks(metrics: list[CandidateMetrics]) -> None:
    """Fill the four *_rank fields with competition ranks. Mutates in place."""
    succ = _competition_rank(metrics, lambda m: m.success_pct, higher_is_better=True)
    fail = _competition_rank(metrics, lambda m: m.failure_pct, higher_is_better=False)  # lower = better
    foll = _competition_rank(metrics, lambda m: m.follower_count, higher_is_better=True)
    # treat "no rating" as worst (-1) so unrated creators rank below rated ones
    rate = _competition_rank(
        metrics,
        lambda m: m.avg_rating if m.avg_rating is not None else -1.0,
        higher_is_better=True,
    )
    for m in metrics:
        m.success_rank = succ[m.creator.id]
        m.failure_rank = fail[m.creator.id]
        m.follower_rank = foll[m.creator.id]
        m.ratings_rank = rate[m.creator.id]


def compute_candidate_metrics(
    ranked: list[tuple[Creator, float]],
) -> list[CandidateMetrics]:
    """For each Stage-2 candidate, pull past gigs and derive metrics.

    `ranked` is the (creator, cosine_score) list from ranker.rank_candidates.
    """
    metrics = []
    for creator, cosine in ranked:
        past = db.recent_completed_gigs_for_creator(creator.id, limit=10)

        successful = sum(1 for g in past if g.outcome == "success")
        failed = sum(1 for g in past if g.outcome in ("failed", "no_response"))
        total = successful + failed

        # % of total — a fair assessment regardless of how many gigs a creator has
        success_pct = successful / total if total > 0 else 0.0
        failure_pct = failed / total if total > 0 else 0.0

        ratings = [g.business_rating for g in past if g.business_rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        metrics.append(CandidateMetrics(
            creator=creator,
            cosine_score=cosine,
            successful_gigs=successful,
            failed_gigs=failed,
            total_gigs=total,
            success_pct=success_pct,
            failure_pct=failure_pct,
            follower_count=creator.follower_count,
            avg_rating=avg_rating,
            recent_gigs=past,
        ))

    _assign_ranks(metrics)
    return metrics

# ============================================================
# 2.3b — prompt formatting
# ============================================================

from pathlib import Path

PROMPT_DIR = Path(__file__).parent.parent / "prompts"
PROMPT_VERSION = "arm2_v1"


def _load_prompt_template(version: str) -> str:
    """Read a versioned prompt template from prompts/."""
    return (PROMPT_DIR / f"{version}.txt").read_text()


def _format_gig_brief(gig: Gig) -> str:
    """The gig as a compact text block for the {gig_brief} placeholder."""
    remote = "remote OK" if gig.remote_acceptable else "on-site only"
    return (
        f"Category: {gig.category}\n"
        f"Subcategories: {', '.join(gig.subcategories)}\n"
        f"Content needed: {', '.join(gig.content_needs)}\n"
        f"Budget: ${gig.budget_range[0]}-${gig.budget_range[1]}\n"
        f"Timeline: {gig.timeline_days} days\n"
        f"Location: {gig.location_required} ({remote})\n"
        f"Niche tags: {', '.join(gig.niche_tags)}"
    )


def _format_candidates_table(metrics: list[CandidateMetrics]) -> str:
    """The candidates as a metrics table for the {candidates_table} placeholder.

    Shows success/failure as a PERCENTAGE of each creator's past gigs (fair
    regardless of gig volume), the gig count (so the LLM can tell 'unproven'
    from 'proven'), follower count, avg rating, and the four ranks.
    Cosine score is omitted — Stage 2 already used it to pick these.
    """
    legend = (
        "(succ%/fail% = share of that creator's past gigs. "
        "ranks: higher = better, max = number of candidates, ties shared. "
        "gigs=0 means an unproven creator, not a bad one.)"
    )
    header = (
        f"{'creator_id':<14} {'gigs':>4} {'succ%':>6} {'fail%':>6} "
        f"{'followers':>10} {'rating':>6} {'rank s/f/fo/r':>16}"
    )
    lines = [legend, "", header]
    for m in metrics:
        rating = f"{m.avg_rating:.1f}" if m.avg_rating is not None else "n/a"
        ranks = f"{m.success_rank}/{m.failure_rank}/{m.follower_rank}/{m.ratings_rank}"
        lines.append(
            f"{m.creator.id:<14} {m.total_gigs:>4} "
            f"{m.success_pct * 100:>5.0f}% {m.failure_pct * 100:>5.0f}% "
            f"{m.follower_count:>10} {rating:>6} {ranks:>16}"
        )
    return "\n".join(lines)


def _format_recent_gigs(metrics: list[CandidateMetrics]) -> str:
    """Per-candidate recent gig history for the {candidates_recent_gigs} placeholder.

    Most candidates have no past gigs (cold-start) — stated explicitly so the
    LLM knows the difference between 'unproven' and 'proven bad'.
    """
    blocks = []
    for m in metrics:
        if not m.recent_gigs:
            blocks.append(f"{m.creator.id}: no past gigs (new / unproven creator)")
            continue
        gig_lines = []
        for g in m.recent_gigs:
            rating = f"rated {g.business_rating}/5" if g.business_rating else "unrated"
            gig_lines.append(f"  - {g.category} gig | outcome={g.outcome} | {rating}")
        blocks.append(
            f"{m.creator.id} ({len(m.recent_gigs)} past gigs):\n" + "\n".join(gig_lines)
        )
    return "\n\n".join(blocks)


def _format_output_schema() -> str:
    """Describe the JSON shape we want back, for the {output_schema} placeholder."""
    return (
        '{\n'
        '  "recommendations": [\n'
        '    {\n'
        '      "creator_id": "<exact id from the candidates table>",\n'
        '      "rank": <1, 2, or 3>,\n'
        '      "reasoning": "<2-3 sentences citing specific metrics>",\n'
        '      "strengths": ["<short phrase>", "..."],\n'
        '      "risks": ["<short phrase>", "..."],\n'
        '      "key_signals": ["<cited fact, e.g. success%=80 over 10 gigs>", "..."]\n'
        '    }\n'
        '  ]\n'
        '}\n'
        'Return EXACTLY 3 recommendation objects, ranked 1, 2, 3.'
    )


def build_prompt(gig: Gig, metrics: list[CandidateMetrics]) -> str:
    """Assemble the full Arm 2 prompt — load the versioned template,
    fill its four placeholders."""
    template = _load_prompt_template(PROMPT_VERSION)
    return template.format(
        gig_brief=_format_gig_brief(gig),
        candidates_table=_format_candidates_table(metrics),
        candidates_recent_gigs=_format_recent_gigs(metrics),
        output_schema=_format_output_schema(),
    )

# ============================================================
# 2.3c — Claude call + response parsing
# ============================================================

import os
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

# Load ANTHROPIC_API_KEY (and MATCHSCOUT_* settings) from the project .env.
load_dotenv(Path(__file__).parent.parent / ".env")

# Anthropic SDK client — picks up ANTHROPIC_API_KEY from the environment.
_client = Anthropic()

# Model + token budget, overridable via .env.
_MODEL = os.environ.get("MATCHSCOUT_MODEL", "claude-sonnet-4-6")
_MAX_TOKENS = int(os.environ.get("MATCHSCOUT_MAX_TOKENS", "2048"))

# Sonnet 4.6 pricing, USD per million tokens — used to cost each call.
_INPUT_COST_PER_MTOK = 3.0
_OUTPUT_COST_PER_MTOK = 15.0


class _LLMRecommendation(BaseModel):
    """One creator pick exactly as the LLM returns it — before our code adds
    system fields (gig_id, generated_at, etc.) in step 2.3d."""
    creator_id: str
    rank: int
    reasoning: str
    strengths: list[str]
    risks: list[str]
    key_signals: list[str]


class _LLMResponse(BaseModel):
    """The full structured payload expected back from Claude."""
    recommendations: list[_LLMRecommendation]


def _extract_json(text: str) -> str:
    """Slice the JSON object out of Claude's text reply.

    Claude usually returns clean JSON, but can wrap it in ```json fences or
    add a sentence first — so we take everything from the first '{' to the
    last '}'.
    """
    # Find the outermost brace pair.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in LLM response: {text[:200]}")
    return text[start : end + 1]


@traceable(name="matchscout_call_llm", run_type="llm")
def call_llm(
    prompt: str, gig_id: str, prompt_version: str
) -> tuple[_LLMResponse, float, str | None, str | None]:
    """Send the assembled prompt to Claude; return the parsed recommendations,
    the dollar cost, plus the LangSmith trace_id + URL for this call.

    The @traceable decorator auto-captures inputs (prompt, gig_id,
    prompt_version), output, latency, and a trace UUID, and ships them to
    LangSmith. We then read the trace's UUID + URL back so they can be
    persisted on the rec rows for dashboard drill-down.

    trace_id and langsmith_url will be None if LANGSMITH_TRACING is unset
    (e.g. when the CI smoke test runs without API keys).
    """
    # One Messages API call — the prompt already carries all instructions.
    response = _client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    # Cost the call from the token usage the API reports back.
    usage = response.usage
    cost = (
        usage.input_tokens / 1_000_000 * _INPUT_COST_PER_MTOK
        + usage.output_tokens / 1_000_000 * _OUTPUT_COST_PER_MTOK
    )

    # Parse the JSON the model returned.
    raw_text = response.content[0].text
    parsed = _LLMResponse.model_validate_json(_extract_json(raw_text))

    # Reach into the active trace to pull its identity + inspector URL.
    # Returns None when tracing is disabled (no API key / env var off).
    run = get_current_run_tree()
    if run is not None:
        trace_id = str(run.id)
        langsmith_url = run.get_url()
    else:
        trace_id = None
        langsmith_url = None

    return parsed, cost, trace_id, langsmith_url


# ============================================================
# 2.3d — recommendation builders + LLM-output validation
# ============================================================
# Stage-3 control flow (arm routing, the retry loop) now lives in
# pipeline.py as part of the unified pipeline graph. This section keeps
# only the pure building blocks that the graph's nodes call.

import uuid
from datetime import datetime
from typing import Optional

from matchscout.schemas import CreatorRecommendation


def validate_llm_response(
    response: _LLMResponse, metrics: list[CandidateMetrics]
) -> Optional[str]:
    """Check the LLM response is usable. Return an error string describing
    the first problem, or None if the response is valid.

    Valid = exactly 3 recommendations, ranks are {1,2,3}, and every
    creator_id is one of the candidates (catches hallucinated IDs).
    """
    valid_ids = {m.creator.id for m in metrics}
    recs = response.recommendations
    if len(recs) != 3:
        return f"expected 3 recommendations, got {len(recs)}"
    if {r.rank for r in recs} != {1, 2, 3}:
        return f"ranks must be 1/2/3, got {sorted(r.rank for r in recs)}"
    unknown = [r.creator_id for r in recs if r.creator_id not in valid_ids]
    if unknown:
        return f"recommended unknown creator_id(s): {unknown}"
    return None


def assemble_recommendations(
    gig: Gig,
    llm_response: _LLMResponse,
    cost: float,
    trace_id: str | None,
    langsmith_url: str | None,
) -> list[CreatorRecommendation]:
    """Turn the validated LLM output into stored CreatorRecommendation objects,
    adding the system fields the LLM doesn't produce.

    Attribution:
      - cost_usd : whole call cost on the rank-1 row, 0 on the others
                   (so SUM(cost_usd) per gig = the gig's true cost)
      - trace_id / langsmith_url : same value on ALL 3 rows
                   (one trace serves all 3 picks; dashboard renders a
                   per-row "View trace" link without needing a JOIN)
    """
    recs = []
    for i, llm_rec in enumerate(llm_response.recommendations):
        recs.append(CreatorRecommendation(
            id=str(uuid.uuid4()),
            gig_id=gig.id,
            creator_id=llm_rec.creator_id,
            rank=llm_rec.rank,
            source_arm="llm",
            prompt_version=PROMPT_VERSION,
            reasoning=llm_rec.reasoning,
            strengths=llm_rec.strengths,
            risks=llm_rec.risks,
            key_signals=llm_rec.key_signals,
            generated_at=datetime.now(),
            cost_usd=cost if i == 0 else 0.0,
            trace_id=trace_id,
            langsmith_url=langsmith_url,
        ))
    return recs



def build_no_llm_recommendations(
    gig: Gig, ranked: list[tuple[Creator, float]]
) -> list[CreatorRecommendation]:
    """Arm 1 — take the top 3 candidates straight from Stage 2's cosine
    ranking. No LLM call, no reasoning."""
    recs = []
    for rank, (creator, _score) in enumerate(ranked[:3], start=1):
        recs.append(CreatorRecommendation(
            id=str(uuid.uuid4()),
            gig_id=gig.id,
            creator_id=creator.id,
            rank=rank,
            source_arm="no_llm",
            prompt_version=None,
            reasoning=None,
            strengths=[],
            risks=[],
            key_signals=[],
            generated_at=datetime.now(),
            cost_usd=0.0,
        ))
    return recs

# ---------- smoke test ----------

if __name__ == "__main__":
    from matchscout.data_loader import load_creators
    from matchscout.filter import filter_candidates
    from matchscout.ranker import rank_candidates

    creators = load_creators()
    gig = ranked = None
    for g in db.list_gigs(status="open"):
        cands = filter_candidates(g, creators)
        if len(cands) < 10:
            continue
        r = rank_candidates(g, cands, top_k=10)
        if any(c.total_gigs > 0 for c in compute_candidate_metrics(r)):
            gig, ranked = g, r
            break

    metrics = compute_candidate_metrics(ranked)

    no_llm = build_no_llm_recommendations(gig, ranked)
    print(f"Arm 1 (no_llm) top 3: {[r.creator_id for r in no_llm]}\n")

    parsed, cost = call_llm(build_prompt(gig, metrics))
    err = validate_llm_response(parsed, metrics)
    print(f"Arm 2 validation: {'OK' if err is None else err}")
    if err is None:
        for r in assemble_recommendations(gig, parsed, cost):
            print(f"  rank {r.rank}: {r.creator_id}  (${r.cost_usd:.4f})")
