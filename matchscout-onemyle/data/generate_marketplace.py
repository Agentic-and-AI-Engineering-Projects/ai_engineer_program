"""
generate_marketplace.py — Synthetic Onemyle marketplace data for MatchScout.

Generates:
  - data/creators.csv      (~400 fake creators)
  - data/businesses.csv    (~300 fake businesses)
  - data/matches.csv       (~150 historical matches with success/failure labels)

Usage:
  python data/generate_marketplace.py
"""

import json
import random
from pathlib import Path
from faker import Faker
from tqdm import tqdm
import pandas as pd

# Reproducible randomness — same seed → same dataset every run
SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# Where we are
DATA_DIR = Path(__file__).parent  # the data/ folder
CATEGORIES_FILE = DATA_DIR / "categories.json"

# Load the category schema we built in Step 2A
with open(CATEGORIES_FILE) as f:
    CATEGORIES = json.load(f)

PRIMARY_CATEGORIES = list(CATEGORIES["primary_categories"].keys())
CONTENT_TYPES = CATEGORIES["content_types"]
LOCATIONS = CATEGORIES["locations"]
ADJACENT_MAP = CATEGORIES["adjacent_categories"]


# Helper — pick N items from a list with replacement
def sample(items, n):
    return random.sample(items, min(n, len(items)))


# Helper — generate a budget range like (low, high)
def gen_budget_range(category):
    """Budget varies by category — luxury/fine dining higher, casual lower."""
    base_low = random.choice([100, 200, 300, 500, 800, 1200])
    spread = random.choice([200, 400, 600, 1000])
    return [base_low, base_low + spread]


# Helper — pick a creator's primary category, with some likely to be cross-category
def pick_creator_categories():
    primary = random.choice(PRIMARY_CATEGORIES)
    # 30% chance of having a secondary (cross-category) skill
    if random.random() < 0.30:
        secondary_options = [c for c in PRIMARY_CATEGORIES if c != primary]
        secondary = [random.choice(secondary_options)]
    else:
        secondary = []
    return primary, secondary


print(f"Loaded {len(PRIMARY_CATEGORIES)} primary categories")
print(f"Categories: {PRIMARY_CATEGORIES}")

# ============================================================
# CREATOR GENERATION
# ============================================================

def generate_creator(creator_id: int) -> dict:
    """Generate one synthetic creator with realistic marketplace attributes."""

    # Categories
    primary_cat, secondary_cats = pick_creator_categories()
    cat_data = CATEGORIES["primary_categories"][primary_cat]

    # Sub-categories (1-3 from the primary category's sub-list)
    n_subcats = random.randint(1, 3)
    subcategories = sample(cat_data["subcategories"], n_subcats)

    # Niche tags (3-6 from the primary category's tag pool)
    n_tags = random.randint(3, 6)
    niche_tags = sample(cat_data["niche_tags"], n_tags)

    # Content types creator can produce (1-3)
    n_content = random.randint(1, 3)
    content_types = sample(CONTENT_TYPES, n_content)

    # Follower count — log-distributed (most small, few huge)
    follower_count = int(10 ** random.uniform(2.5, 5.5))  # 316 to ~316K

    # Engagement rate — typically 1-8%
    engagement_rate = round(random.uniform(0.01, 0.08), 4)

    # Past gigs — newer creators have fewer
    past_gigs = random.choice([0, 0, 1, 2, 5, 10, 20, 30, 50])

    # Avg rating — skewed toward positive (most creators are 4+)
    avg_rating = round(random.choice([3.5, 4.0, 4.2, 4.5, 4.7, 4.8, 5.0]), 1) if past_gigs > 0 else None

    # Budget range
    budget_low, budget_high = gen_budget_range(primary_cat)

    # Location
    location = random.choice(LOCATIONS)

    # Most creators are open to remote work
    remote_friendly = random.random() < 0.75

    # Response time — most respond within hours, some take days
    response_time_hours = round(random.uniform(0.5, 48), 1)

    # Active in last 30 days — 80% are active
    active_30d = random.random() < 0.80

    return {
        "id": f"creator_{creator_id:04d}",
        "name": fake.name(),
        "primary_category": primary_cat,
        "primary_subcategories": subcategories,
        "secondary_categories": secondary_cats,
        "content_types": content_types,
        "location": location,
        "remote_friendly": remote_friendly,
        "follower_count": follower_count,
        "engagement_rate": engagement_rate,
        "past_gigs_completed": past_gigs,
        "avg_rating": avg_rating,
        "budget_range_per_gig": [budget_low, budget_high],
        "niche_tags": niche_tags,
        "response_time_hours_avg": response_time_hours,
        "active_in_last_30_days": active_30d,
    }


def generate_creators(n: int = 400) -> list[dict]:
    """Generate N creators with a progress bar."""
    print(f"\nGenerating {n} creators...")
    return [generate_creator(i) for i in tqdm(range(1, n + 1))]

# ============================================================
# BUSINESS GENERATION
# ============================================================

def generate_business(business_id: int) -> dict:
    """Generate one synthetic business with realistic marketplace attributes."""

    # Pick a category
    primary_cat = random.choice(PRIMARY_CATEGORIES)
    cat_data = CATEGORIES["primary_categories"][primary_cat]

    # Sub-categories (1-2 — businesses are usually narrower than creators)
    n_subcats = random.randint(1, 2)
    subcategories = sample(cat_data["subcategories"], n_subcats)

    # Niche tags (3-5)
    n_tags = random.randint(3, 5)
    niche_tags = sample(cat_data["niche_tags"], n_tags)

    # What content does this business need? (1-3 types)
    n_needs = random.randint(1, 3)
    content_needs = sample(CONTENT_TYPES, n_needs)

    # Business size (small/medium/large) — affects budget and creator preference
    business_size = random.choices(
        ["small", "medium", "large"],
        weights=[60, 30, 10]  # most are small
    )[0]

    # Budget range based on size
    if business_size == "small":
        budget_low = random.choice([200, 300, 500])
        budget_high = budget_low + random.choice([300, 500, 700])
    elif business_size == "medium":
        budget_low = random.choice([500, 800, 1000])
        budget_high = budget_low + random.choice([500, 1000, 1500])
    else:  # large
        budget_low = random.choice([1500, 2000, 3000])
        budget_high = budget_low + random.choice([2000, 3000, 5000])

    # Past creators hired
    past_creators = random.choice([0, 0, 1, 2, 5, 8, 15, 30])

    # Avg creator rating they've given
    avg_creator_rating = round(random.choice([3.5, 4.0, 4.3, 4.5, 4.7]), 1) if past_creators > 0 else None

    # Location
    location = random.choice(LOCATIONS)

    # Remote acceptable? Some businesses need on-site (restaurants), some don't (online retailers)
    on_site_categories = {"food_beverage", "auto", "beauty_wellness", "fitness_sports", "travel_hospitality"}
    if primary_cat in on_site_categories:
        remote_acceptable = random.random() < 0.20  # mostly need on-site
    else:
        remote_acceptable = random.random() < 0.65  # often OK with remote

    # Currently has open gigs?
    current_gigs_open = random.choice([0, 0, 1, 1, 2, 3, 5])

    # Active in last 30 days
    active_30d = random.random() < 0.85

    # Preferred creator follower size
    preferred_creator_size = random.choices(
        ["small", "mid", "large", "any"],
        weights=[20, 35, 15, 30]
    )[0]

    return {
        "id": f"biz_{business_id:04d}",
        "name": fake.company(),
        "primary_category": primary_cat,
        "primary_subcategories": subcategories,
        "secondary_categories": [],  # businesses usually stay in one category
        "content_needs": content_needs,
        "location": location,
        "remote_acceptable": remote_acceptable,
        "business_size": business_size,
        "past_creators_hired": past_creators,
        "avg_creator_rating": avg_creator_rating,
        "budget_range_per_gig": [budget_low, budget_high],
        "niche_tags": niche_tags,
        "current_gigs_open": current_gigs_open,
        "active_in_last_30_days": active_30d,
        "preferred_creator_size": preferred_creator_size,
    }


def generate_businesses(n: int = 300) -> list[dict]:
    """Generate N businesses with a progress bar."""
    print(f"\nGenerating {n} businesses...")
    return [generate_business(i) for i in tqdm(range(1, n + 1))]

# ============================================================
# HISTORICAL MATCH GENERATION (the golden set + general history)
# ============================================================

def categories_compatible(creator: dict, business: dict) -> bool:
    """Reusable filter — same as Stage 1 we'll build later."""
    if creator["primary_category"] == business["primary_category"]:
        return True
    if creator["primary_category"] in ADJACENT_MAP.get(business["primary_category"], []):
        return True
    if business["primary_category"] in creator["secondary_categories"]:
        return True
    return False

def estimate_match_quality(creator: dict, business: dict) -> float:
    """
    Heuristic to score a match before deciding if it succeeded.
    Used only to make synthetic outcomes realistic — NOT what the AI uses.
    Returns 0.0 to 1.0.
    """
    score = 0.0

    # Category match
    if creator["primary_category"] == business["primary_category"]:
        score += 0.30
    elif creator["primary_category"] in ADJACENT_MAP.get(business["primary_category"], []):
        score += 0.15

    # Sub-category overlap
    overlap = set(creator["primary_subcategories"]) & set(business["primary_subcategories"])
    if overlap:
        score += 0.15

    # Niche tag overlap
    tag_overlap = set(creator["niche_tags"]) & set(business["niche_tags"])
    score += min(len(tag_overlap) * 0.05, 0.15)

    # Content type overlap
    if set(creator["content_types"]) & set(business["content_needs"]):
        score += 0.10

    # Location match
    if creator["location"] == business["location"]:
        score += 0.10
    elif creator["remote_friendly"] and business["remote_acceptable"]:
        score += 0.05

    # Budget overlap
    c_lo, c_hi = creator["budget_range_per_gig"]
    b_lo, b_hi = business["budget_range_per_gig"]
    if c_hi >= b_lo and c_lo <= b_hi:  # ranges overlap
        score += 0.10

    # Creator track record
    if creator["past_gigs_completed"] >= 5 and (creator["avg_rating"] or 0) >= 4.0:
        score += 0.05

    return min(score, 1.0)

def generate_match(match_id: int, creator: dict, business: dict) -> dict:
    """Generate one historical match record with realistic outcome."""

    quality_score = estimate_match_quality(creator, business)

    # Outcome distribution depends on quality
    # High quality (>0.7) → mostly successful
    # Medium (0.4-0.7) → mixed
    # Low (<0.4) → mostly failed/no_response
    if quality_score > 0.7:
        outcome = random.choices(
            ["successful", "failed", "no_response"],
            weights=[75, 15, 10]
        )[0]
    elif quality_score > 0.4:
        outcome = random.choices(
            ["successful", "failed", "no_response"],
            weights=[40, 35, 25]
        )[0]
    else:
        outcome = random.choices(
            ["successful", "failed", "no_response"],
            weights=[15, 35, 50]
        )[0]

    # Outcome-specific reason text
    # Outcome severity correlates with quality score
    # Reasons + ratings + gig_count + total_paid all gated by quality
    if outcome == "successful":
        if quality_score > 0.6:
            # High-quality success — unlocks deep collaboration
            outcome_reason = random.choice([
                "completed_multiple_gigs_excellent_reviews",
                "ongoing_collaboration",
                "repeat_business",
                "completed_first_gig_business_re_engaged",
            ])
            creator_rating = random.choices([4, 5], weights=[15, 85])[0]
            business_rating = random.choices([4, 5], weights=[20, 80])[0]
            gig_count = random.choice([1, 2, 3, 5])
        else:
            # Low-quality success — single gig only, ratings lower
            outcome_reason = random.choice([
                "completed_first_gig_no_repeat",
                "single_gig_acceptable_quality",
                "completed_first_gig_business_re_engaged",
            ])
            creator_rating = random.choices([3, 4, 5], weights=[20, 60, 20])[0]
            business_rating = random.choices([3, 4, 5], weights=[25, 55, 20])[0]
            gig_count = 1

        # total_paid = gigs × midpoint of creator's budget range
        avg_gig_value = (creator["budget_range_per_gig"][0] + creator["budget_range_per_gig"][1]) // 2
        total_paid = gig_count * avg_gig_value

    elif outcome == "failed":
        outcome_reason = random.choice([
            "completed_first_gig_quality_below_expectations",
            "creator_unresponsive_after_intro",
            "budget_negotiation_failed",
            "scope_misalignment",
            "single_gig_no_repeat",
        ])
        creator_rating = None
        business_rating = None
        gig_count = 1  # they tried at least once
        # Paid for the one gig that happened
        total_paid = creator["budget_range_per_gig"][0]

    else:  # no_response
        outcome_reason = random.choice([
            "creator_did_not_apply",
            "business_did_not_respond_to_pitch",
            "no_engagement_after_intro",
        ])
        creator_rating = None
        business_rating = None
        gig_count = 0
        total_paid = 0

    return {
        "id": f"match_{match_id:04d}",
        "creator_id": creator["id"],
        "business_id": business["id"],
        "introduced_at": fake.date_between(start_date="-1y", end_date="-30d").isoformat(),
        "outcome": outcome,
        "outcome_reason": outcome_reason,
        "creator_rating": creator_rating,
        "business_rating": business_rating,
        "gig_count": gig_count,
        "total_paid": total_paid,
        "synthetic_quality_score": round(quality_score, 2),  # for our reference only
    }

def generate_matches(creators: list, businesses: list, n: int = 150) -> list[dict]:
    """
    Generate N historical matches.
    Mix: 70% category-compatible (likely to be tried), 30% random (cross-category attempts).
    """
    print(f"\nGenerating {n} historical matches...")
    matches = []

    # 70% from category-compatible pairs
    n_compatible = int(n * 0.7)
    for i in tqdm(range(n_compatible), desc="Compatible matches"):
        # Pick a random business, then find a creator that fits
        business = random.choice(businesses)
        compatible_creators = [c for c in creators if categories_compatible(c, business)]
        if not compatible_creators:
            continue
        creator = random.choice(compatible_creators)
        matches.append(generate_match(i + 1, creator, business))

    # 30% random pairs (some will fail, demonstrating bad matches)
    n_random = n - len(matches)
    for i in tqdm(range(n_random), desc="Random matches"):
        creator = random.choice(creators)
        business = random.choice(businesses)
        matches.append(generate_match(len(matches) + 1, creator, business))

    return matches

# ============================================================
# MAIN — Generate everything and save to CSV
# ============================================================

if __name__ == "__main__":
    creators = generate_creators(400)
    businesses = generate_businesses(300)
    matches = generate_matches(creators, businesses, 150)

    # Save to CSV
    pd.DataFrame(creators).to_csv(DATA_DIR / "creators.csv", index=False)
    pd.DataFrame(businesses).to_csv(DATA_DIR / "businesses.csv", index=False)
    pd.DataFrame(matches).to_csv(DATA_DIR / "matches.csv", index=False)





