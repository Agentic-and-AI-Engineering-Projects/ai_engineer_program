"""
Stage 1 of the MatchScout pipeline — deterministic hard filter.

Given a Gig and the full creator catalog, return the creators that pass
three structural rules: location, budget, content-type. No LLM, no
embeddings — pure boolean logic. Narrows the catalog before the
expensive Stage 2 / Stage 3 run.
"""

from matchscout.schemas import Gig, Creator


# ---------- one helper per rule ----------

def _location_compatible(creator: Creator, gig: Gig) -> bool:
    """Same metro, OR the gig is location-agnostic, OR both sides do remote."""
    if gig.location_required == "any":
        return True
    if creator.location == gig.location_required:
        return True
    if creator.remote_friendly and gig.remote_acceptable:
        return True
    return False


def _budget_overlaps(creator: Creator, gig: Gig) -> bool:
    """Creator's price range and the gig's budget range intersect."""
    creator_low, creator_high = creator.budget_range_per_gig
    gig_low, gig_high = gig.budget_range
    # Two ranges overlap iff each one's low is <= the other's high.
    return creator_low <= gig_high and gig_low <= creator_high


def _content_type_overlaps(creator: Creator, gig: Gig) -> bool:
    """At least one shared content type between what the creator
    produces and what the gig needs."""
    return bool(set(creator.content_types) & set(gig.content_needs))


# ---------- the public Stage 1 function ----------

def filter_candidates(gig: Gig, creators: dict[str, Creator]) -> list[Creator]:
    """Return the creators that pass ALL three hard rules for this gig."""
    passed = []
    for creator in creators.values():
        if not _location_compatible(creator, gig):
            continue
        if not _budget_overlaps(creator, gig):
            continue
        if not _content_type_overlaps(creator, gig):
            continue
        passed.append(creator)
    return passed


# ---------- smoke test ----------

if __name__ == "__main__":
    from matchscout.data_loader import load_creators
    from matchscout import db

    creators = load_creators()
    open_gigs = db.list_gigs(status="open")
    sample_gig = open_gigs[0]

    candidates = filter_candidates(sample_gig, creators)

    print(f"Gig {sample_gig.id}:")
    print(f"  category={sample_gig.category}  location={sample_gig.location_required}")
    print(f"  budget={sample_gig.budget_range}  needs={sample_gig.content_needs}")
    print(f"  remote_acceptable={sample_gig.remote_acceptable}")
    print(f"\n  {len(creators)} creators -> {len(candidates)} passed Stage 1 filter")
