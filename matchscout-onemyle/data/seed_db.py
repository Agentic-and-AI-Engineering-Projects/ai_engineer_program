"""
seed_db.py — One-time database seeding for MatchScout.

Two jobs:
  1. Load matches.csv into the gigs table as historical completed/failed gigs.
  2. Generate ~30 synthetic open gigs for the pipeline to process.

Run once (from matchscout-onemyle/):  python data/seed_db.py
Idempotent: refuses to run if the gigs table is already populated.
"""

import sys
import random
import hashlib          # ← add this line
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# This script lives in data/ but imports the matchscout package —
# add the project root to sys.path so `import matchscout` resolves.
sys.path.insert(0, str(Path(__file__).parent.parent))

from matchscout import db
from matchscout.data_loader import load_businesses
from matchscout.schemas import Gig

DATA_DIR = Path(__file__).parent
SEED = 42
random.seed(SEED)


# matches.csv `outcome` → (gig.status, gig.outcome)
_OUTCOME_MAP = {
    "successful":  ("completed", "success"),
    "failed":      ("failed",    "failed"),
    "no_response": ("failed",    "no_response"),
}


def seed_past_gigs() -> list[Gig]:
    """Convert each matches.csv row into a historical Gig.

    A 'match' is a concluded creator-business collaboration. The gig's
    category / location / budget come from the business that posted it.
    """
    businesses = load_businesses()
    df = pd.read_csv(DATA_DIR / "matches.csv")

    gigs = []
    for _, row in df.iterrows():
        biz = businesses.get(row["business_id"])
        if biz is None:
            continue  # skip a match referencing a missing business

        status, outcome = _OUTCOME_MAP[row["outcome"]]
        introduced = datetime.fromisoformat(row["introduced_at"])
        timeline = random.choice([7, 14, 21, 30])

        gig = Gig(
            id=f"gig_h{row['id'].split('_')[-1]}",      # match_0001 -> gig_h0001
            business_id=biz.id,
            posted_at=introduced,
            status=status,
            category=biz.primary_category,
            subcategories=biz.primary_subcategories,
            content_needs=biz.content_needs,
            budget_range=biz.budget_range_per_gig,
            timeline_days=timeline,
            location_required=biz.location,
            remote_acceptable=biz.remote_acceptable,
            niche_tags=biz.niche_tags,
            treatment_arm=None,                          # historical — predates the A/B
            assigned_creator_id=row["creator_id"],
            outcome=outcome,
            business_rating=row["business_rating"] if pd.notna(row["business_rating"]) else None,
            creator_rating=row["creator_rating"] if pd.notna(row["creator_rating"]) else None,
            completed_at=introduced + timedelta(days=timeline),
        )
        gigs.append(gig)
    return gigs


def generate_open_gigs(n: int = 30, min_candidates: int = 3) -> list[Gig]:
    """Generate N fresh open gigs, each guaranteed to yield at least
    min_candidates after Stage 1 filtering — so every demo gig actually
    exercises the pipeline. (0-candidate gigs produce no recommendation
    and are useless for the demo.)"""
    from matchscout.filter import filter_candidates
    from matchscout.data_loader import load_creators

    businesses = list(load_businesses().values())
    creators = load_creators()
    now = datetime.now()

    gigs = []
    attempts = 0
    while len(gigs) < n and attempts < n * 50:
        attempts += 1
        biz = random.choice(businesses)
        candidate_gig = Gig(
            id=f"gig_open_{len(gigs) + 1:03d}",
            business_id=biz.id,
            posted_at=now - timedelta(days=random.randint(0, 5)),
            status="open",
            category=biz.primary_category,
            subcategories=biz.primary_subcategories,
            content_needs=biz.content_needs,
            budget_range=biz.budget_range_per_gig,
            timeline_days=random.choice([7, 14, 21, 30]),
            location_required=biz.location,
            remote_acceptable=biz.remote_acceptable,
            niche_tags=biz.niche_tags,
        )
        # viability check — only keep gigs that have something to recommend
        if len(filter_candidates(candidate_gig, creators)) >= min_candidates:
            gigs.append(candidate_gig)
    return gigs

def _creator_reliability(creator_id: str) -> float:
    """Return a stable hidden 'reliability' score in [0.15, 0.95] for a creator.

    Derived deterministically from the creator id (via a hash) rather than a
    random draw — so Phase 4's outcome simulation can recompute the exact same
    value. Reliability drives how a creator's gig outcomes are weighted: a
    high-reliability creator mostly succeeds, a low one mostly fails. This is
    what makes a creator's past success rate genuinely predict future quality.
    """
    # Hash the id to a large integer, then map it into the [0.15, 0.95] range.
    digest = int(hashlib.md5(creator_id.encode()).hexdigest(), 16)
    return 0.15 + (digest % 1000) / 1000 * 0.80


def generate_historical_gigs(n: int = 450) -> list[Gig]:
    """Generate N extra synthetic historical gigs (completed / failed).

    Supplements the 150 gigs from matches.csv so creators accumulate enough
    track record for Stage 3's LLM to reason over. Outcomes are drawn from
    each creator's hidden reliability — so past success rate is real signal.
    """
    from matchscout.data_loader import load_creators

    # Load the catalog: creators we assign gigs to, businesses that post them.
    creators = list(load_creators().values())
    businesses = list(load_businesses().values())

    # Index businesses by primary category, so every generated gig pairs a
    # creator with a business in the SAME category — a plausible collaboration.
    biz_by_category: dict[str, list] = {}
    for b in businesses:
        biz_by_category.setdefault(b.primary_category, []).append(b)

    # Give each creator an 'activity weight' — how often they take gigs.
    # Weighted sampling means some creators build a rich history while others
    # stay sparse, mimicking a real marketplace's power-law distribution.
    activity_weights = [random.random() for _ in creators]

    now = datetime.now()
    gigs = []
    for i in range(1, n + 1):
        # Pick a creator, weighted by activity (active creators chosen more often).
        creator = random.choices(creators, weights=activity_weights, k=1)[0]

        # Pick a business in the creator's own category for a plausible gig.
        pool = biz_by_category.get(creator.primary_category)
        if not pool:
            continue
        biz = random.choice(pool)

        # Draw the outcome from this creator's hidden reliability:
        # high reliability -> mostly success, low -> mostly failed / no_response.
        r = _creator_reliability(creator.id)
        outcome = random.choices(
            ["success", "failed", "no_response"],
            weights=[r, (1 - r) * 0.65, (1 - r) * 0.35],
        )[0]

        # status: a success is 'completed'; a failure or no-show is 'failed'.
        status = "completed" if outcome == "success" else "failed"

        # Ratings: strong for a success, poor for a failure, none for a
        # no_response (the collaboration never actually happened).
        if outcome == "success":
            business_rating = float(random.choice([4, 4, 5, 5, 5]))
            creator_rating = float(random.choice([4, 4, 5, 5]))
        elif outcome == "failed":
            business_rating = float(random.choice([1, 2, 2, 3]))
            creator_rating = float(random.choice([1, 2, 3, 3]))
        else:  # no_response
            business_rating = None
            creator_rating = None

        # Random posting date within the last ~18 months; concluded after the timeline.
        posted = now - timedelta(days=random.randint(30, 540))
        timeline = random.choice([7, 14, 21, 30])

        # Build the Gig. Historical gigs predate the experiment, so treatment_arm=None.
        gigs.append(Gig(
            id=f"gig_x{i:04d}",
            business_id=biz.id,
            posted_at=posted,
            status=status,
            category=biz.primary_category,
            subcategories=biz.primary_subcategories,
            content_needs=biz.content_needs,
            budget_range=biz.budget_range_per_gig,
            timeline_days=timeline,
            location_required=biz.location,
            remote_acceptable=biz.remote_acceptable,
            niche_tags=biz.niche_tags,
            treatment_arm=None,
            assigned_creator_id=creator.id,
            outcome=outcome,
            business_rating=business_rating,
            creator_rating=creator_rating,
            completed_at=posted + timedelta(days=timeline),
        ))
    return gigs



if __name__ == "__main__":
    db.init_schema()

    existing = db.list_gigs()
    if existing:
        print(f"gigs table already has {len(existing)} rows — skipping seed.")
        print("To re-seed: delete data/matchscout.db and re-run this script.")
    else:
        # Build all three sets of gigs in memory, then bulk-insert.
        past = seed_past_gigs()                 # 150 from matches.csv
        extra = generate_historical_gigs(450)   # synthetic, reliability-driven
        open_gigs = generate_open_gigs(30)      # the gigs the pipeline will process

        db.insert_gigs(past)
        db.insert_gigs(extra)
        db.insert_gigs(open_gigs)

        print(f"Seeded {len(past)} matches.csv gigs + {len(extra)} synthetic "
              f"historical gigs + {len(open_gigs)} open gigs.")
        print(f"  Total gigs: {len(db.list_gigs())}")
        print(f"  Completed:  {len(db.list_gigs(status='completed'))}")
        print(f"  Failed:     {len(db.list_gigs(status='failed'))}")
        print(f"  Open:       {len(db.list_gigs(status='open'))}")
