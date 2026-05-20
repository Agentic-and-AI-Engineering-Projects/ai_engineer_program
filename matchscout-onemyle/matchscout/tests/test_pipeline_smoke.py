
"""
test_pipeline_smoke.py — Phase 3 CI smoke test.

Not an eval. Proves the pipeline still RUNS and still produces schema-valid
output. Runs the no-LLM path so CI needs no API key and stays fast and
deterministic. Calls the pure stage functions directly (NOT
recommend_creators) so the test mutates no DB rows and is fully repeatable.
"""

import pytest

from matchscout import db
from matchscout.data_loader import load_creators
from matchscout.filter import filter_candidates
from matchscout.ranker import rank_candidates
from matchscout.agent import build_no_llm_recommendations
from matchscout.schemas import CreatorRecommendation


@pytest.fixture(scope="module")
def sample_gig():
    """Pick any gig from the seeded DB to drive the pipeline.

    Status doesn't matter — we only read the gig, we never persist anything,
    so an 'in_review' gig (left over from Phase 2) works fine."""
    gigs = db.list_gigs()
    if not gigs:
        pytest.skip("matchscout.db has no gigs — run seed_db.py first")
    return gigs[0]


def test_filter_returns_candidates(sample_gig):
    """Stage 1 must return at least one candidate for a viable gig."""
    creators = load_creators()
    candidates = filter_candidates(sample_gig, creators)
    assert len(candidates) >= 1


def test_pipeline_no_llm_arm_produces_three_valid_recs(sample_gig):
    """End-to-end no-LLM path: filter -> rank -> build 3 recs."""
    # Stage 1: hard filter.
    creators = load_creators()
    candidates = filter_candidates(sample_gig, creators)
    assert candidates, "no candidates passed Stage 1"

    # Stage 2: cosine ranking, top 10.
    ranked = rank_candidates(sample_gig, candidates, top_k=10)
    assert ranked, "ranker returned nothing"

    # Stage 3 (Arm 1): top 3 by cosine, no LLM.
    recs = build_no_llm_recommendations(sample_gig, ranked)

    # --- the smoke assertions ---
    # Exactly 3 recommendations.
    assert len(recs) == 3
    # Each is a real CreatorRecommendation instance (schema valid).
    assert all(isinstance(r, CreatorRecommendation) for r in recs)
    # Ranks are exactly {1, 2, 3}.
    assert {r.rank for r in recs} == {1, 2, 3}
    # Every recommended creator_id is a real creator.
    assert all(r.creator_id in creators for r in recs)
    # No duplicate creators in one gig's recommendations.
    assert len({r.creator_id for r in recs}) == 3
    # no_llm arm: tagged correctly, no cost, no reasoning.
    assert all(r.source_arm == "no_llm" for r in recs)
    assert all(r.cost_usd == 0.0 for r in recs)
    assert all(r.reasoning is None for r in recs)
    # All point back at the gig we ran.
    assert all(r.gig_id == sample_gig.id for r in recs)
