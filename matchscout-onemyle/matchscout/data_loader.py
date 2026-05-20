
"""
Loads creators, businesses, and historical matches from CSV files
into Pydantic models. The rest of the pipeline works with typed objects.
"""

import json
import pandas as pd
from pathlib import Path
from matchscout.schemas import Creator, Business

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Module-level caches — load once, reuse
_creators_cache: dict[str, Creator] | None = None
_businesses_cache: dict[str, Business] | None = None
_categories_cache: dict | None = None


def load_categories() -> dict:
    """Load the 8-category schema from categories.json."""
    global _categories_cache
    if _categories_cache is None:
        with open(DATA_DIR / "categories.json") as f:
            _categories_cache = json.load(f)
    return _categories_cache


def _parse_list_column(value):
    """CSV serializes lists as Python-repr strings like "['a', 'b']" — parse back to list."""
    if pd.isna(value) or value == "":
        return []
    if isinstance(value, list):
        return value
    # eval is safe here because the CSV came from our own pandas dump
    return eval(value)


def load_creators() -> dict[str, Creator]:
    """Load all creators from creators.csv into a dict keyed by id."""
    global _creators_cache
    if _creators_cache is not None:
        return _creators_cache

    df = pd.read_csv(DATA_DIR / "creators.csv")

    # Parse list-typed columns from their string representations
    list_cols = ["primary_subcategories", "secondary_categories", "content_types",
                 "budget_range_per_gig", "niche_tags"]
    for col in list_cols:
        df[col] = df[col].apply(_parse_list_column)

    # Convert each row to a Creator instance
    creators = {}
    for _, row in df.iterrows():
        c = Creator(**row.to_dict())
        creators[c.id] = c

    _creators_cache = creators
    print(f"Loaded {len(creators)} creators")
    return creators


def load_businesses() -> dict[str, Business]:
    """Load all businesses from businesses.csv into a dict keyed by id."""
    global _businesses_cache
    if _businesses_cache is not None:
        return _businesses_cache

    df = pd.read_csv(DATA_DIR / "businesses.csv")

    list_cols = ["primary_subcategories", "secondary_categories", "content_needs",
                 "budget_range_per_gig", "niche_tags"]
    for col in list_cols:
        df[col] = df[col].apply(_parse_list_column)

    businesses = {}
    for _, row in df.iterrows():
        b = Business(**row.to_dict())
        businesses[b.id] = b

    _businesses_cache = businesses
    print(f"Loaded {len(businesses)} businesses")
    return businesses


def get_creator(creator_id: str) -> Creator:
    """Fetch one creator by ID. Raises KeyError if not found."""
    return load_creators()[creator_id]


def get_business(business_id: str) -> Business:
    """Fetch one business by ID. Raises KeyError if not found."""
    return load_businesses()[business_id]


# Smoke test — run this file directly to verify loading works
if __name__ == "__main__":
    creators = load_creators()
    businesses = load_businesses()
    cats = load_categories()

    print(f"\nCategory schema loaded: {len(cats['primary_categories'])} primary categories")

    # Show sample
    sample_creator = next(iter(creators.values()))
    print(f"\nSample creator (typed Pydantic object):")
    print(f"  {sample_creator.id}: {sample_creator.name}")
    print(f"  Category: {sample_creator.primary_category}")
    print(f"  Niche tags: {sample_creator.niche_tags}")
    print(f"  Budget: ${sample_creator.budget_range_per_gig[0]}-${sample_creator.budget_range_per_gig[1]}")

    sample_business = next(iter(businesses.values()))
    print(f"\nSample business:")
    print(f"  {sample_business.id}: {sample_business.name}")
    print(f"  Category: {sample_business.primary_category}")
    print(f"  Needs: {sample_business.content_needs}")
