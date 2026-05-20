"""
Pydantic schemas for MatchScout entities.

Catalog (loaded from CSV, treated as immutable):
  Creator, Business — intrinsic fields only, no time-varying aggregates.
  Aggregate counts (past gigs completed, avg rating, etc.) are computed
  on demand from the gigs table — never duplicated on the catalog entity.

Operational data (lives in SQLite, mutable):
  Gig — one row per posted gig, status field tracks lifecycle from
    'open' through 'completed'/'failed'/'cancelled'.
  CreatorRecommendation — 3 rows per gig (the system's top 3 picks).
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from datetime import datetime


# Allow loading from CSVs that may have extra columns we no longer use
# (past_gigs_completed, avg_rating, etc. were dropped — silently ignore them).
_loose_config = ConfigDict(extra="ignore")


class Creator(BaseModel):
    """One creator from the marketplace catalog. Intrinsic fields only."""
    model_config = _loose_config

    id: str
    name: str
    primary_category: str
    primary_subcategories: list[str]
    secondary_categories: list[str]
    content_types: list[str]
    location: str
    remote_friendly: bool
    follower_count: int
    engagement_rate: float
    budget_range_per_gig: list[int]   # [low, high]
    niche_tags: list[str]
    active_in_last_30_days: bool
    profile_description: str = ""     # Instagram-bio style; "" until generated


class Business(BaseModel):
    """One business from the marketplace catalog. Intrinsic fields only."""
    model_config = _loose_config

    id: str
    name: str
    primary_category: str
    primary_subcategories: list[str]
    secondary_categories: list[str]
    content_needs: list[str]
    location: str
    remote_acceptable: bool
    business_size: Literal["small", "medium", "large"]
    budget_range_per_gig: list[int]
    niche_tags: list[str]
    active_in_last_30_days: bool
    preferred_creator_size: Literal["small", "mid", "large", "any"]
    profile_description: str = ""


class Gig(BaseModel):
    """
    A job posted by a business. Status field tracks the full lifecycle —
    open / in_review / in_progress / completed / failed / cancelled.
    Historical gigs and active gigs live in the same table, distinguished
    only by status.
    """
    id: str
    business_id: str
    posted_at: datetime
    status: Literal[
        "open",          # newly posted, no creator assigned yet
        "in_review",     # recommendations made, business hasn't picked
        "in_progress",   # creator assigned, work happening
        "completed",     # work done, outcome=success or failed or no_response
        "failed",        # explicit failure status
        "cancelled",     # business pulled the gig
    ]

    # What the gig asks for
    category: str
    subcategories: list[str]
    content_needs: list[str]
    budget_range: list[int]               # [low, high]
    timeline_days: int
    location_required: str                # specific city or "any"
    remote_acceptable: bool
    niche_tags: list[str]

    # Experimental assignment (set when the pipeline runs)
    treatment_arm: Optional[Literal["no_llm", "llm"]] = None

    # Filled when the business picks a creator and work concludes
    assigned_creator_id: Optional[str] = None
    outcome: Optional[Literal["success", "failed", "no_response"]] = None
    business_rating: Optional[float] = None   # 1-5, business rating the creator
    creator_rating: Optional[float] = None    # 1-5, creator rating the business
    completed_at: Optional[datetime] = None


class CreatorRecommendation(BaseModel):
    """
    One row per (gig, creator) recommendation. Three rows written per gig.
    Reasoning/strengths/risks are populated for Arm 2; null for Arm 1.
    """
    id: str
    gig_id: str
    creator_id: str
    rank: int                                  # 1, 2, or 3
    source_arm: Literal["no_llm", "llm"]
    prompt_version: Optional[str] = None       # e.g. "arm2_v1"; null for no_llm
    reasoning: Optional[str] = None            # null for no_llm
    strengths: list[str] = []
    risks: list[str] = []
    key_signals: list[str] = []                # cited facts (e.g., "successful_gigs=8")
    generated_at: datetime
    cost_usd: float = 0.0
