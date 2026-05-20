"""
Stage 2 of the MatchScout pipeline — vector similarity ranking.

Takes the Stage 1 survivors and ranks them by semantic similarity to the
gig-posting business. A small local sentence-transformer embeds each
side's profile text; cosine similarity scores the match.

No LLM, no API cost — the model runs locally.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from matchscout.schemas import Gig, Creator
from matchscout.data_loader import load_businesses

# Load the embedding model once at import time.
# First run downloads ~80MB; cached locally afterwards.
_model = SentenceTransformer("all-MiniLM-L6-v2")


def _embedding_text(entity) -> str:
    """Build one string representing a creator or business for embedding.

    Both Creator and Business expose these five fields — so this function
    is symmetric across the two sides of the marketplace.
    """
    return " ".join([
        " ".join(entity.niche_tags),
        entity.profile_description,
        entity.primary_category,
        " ".join(entity.secondary_categories),
        " ".join(entity.primary_subcategories),
    ])


def rank_candidates(
    gig: Gig,
    candidates: list[Creator],
    top_k: int = 10,
) -> list[tuple[Creator, float]]:
    """Rank Stage 1 candidates by cosine similarity to the gig-posting
    business. Returns (creator, score) pairs, highest score first,
    truncated to top_k."""
    if not candidates:
        return []

    business = load_businesses()[gig.business_id]

    # Embed the business (one vector) and every candidate (one vector each)
    business_vec = _model.encode(_embedding_text(business))
    candidate_vecs = _model.encode([_embedding_text(c) for c in candidates])

    # Cosine similarity of the business against each candidate → array of scores
    scores = cosine_similarity([business_vec], candidate_vecs)[0]

    # Pair each creator with its score, sort descending, take top_k
    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    return [(creator, float(score)) for creator, score in ranked[:top_k]]


# ---------- smoke test ----------

if __name__ == "__main__":
    from matchscout.data_loader import load_creators
    from matchscout import db
    from matchscout.filter import filter_candidates

    creators = load_creators()

    # pick the first open gig with a healthy candidate pool
    for g in db.list_gigs(status="open"):
        cands = filter_candidates(g, creators)
        if len(cands) >= 20:
            gig, candidates = g, cands
            break

    ranked = rank_candidates(gig, candidates, top_k=10)

    print(f"Gig {gig.id}: {len(candidates)} candidates -> top {len(ranked)} by cosine\n")
    for rank, (creator, score) in enumerate(ranked, start=1):
        print(f"  {rank:2d}. {creator.id}  score={score:.3f}  "
              f"{creator.primary_category}  tags={creator.niche_tags[:3]}")
