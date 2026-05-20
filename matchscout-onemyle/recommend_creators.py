"""
recommend_creators.py — CLI entry point for the MatchScout pipeline.

The PoC stand-in for a future "Recommend Creators" button: a business
posts a gig, this command runs the full pipeline for it.

Usage:
    python recommend_creators.py --gig-id gig_open_002
    python recommend_creators.py --all          # process every open gig
"""

import argparse

from matchscout import db
from matchscout.pipeline import recommend_creators


def _print_recommendations(gig_id: str, recs: list) -> None:
    """Print one gig's recommendations in a readable form."""
    arm = db.get_gig(gig_id).treatment_arm
    print(f"\n{gig_id}  [arm: {arm}]  — {len(recs)} recommendations:")
    for rec in recs:
        print(f"  rank {rec.rank}: {rec.creator_id}  (${rec.cost_usd:.4f})")
        if rec.reasoning:
            print(f"    {rec.reasoning[:120]}...")


def main() -> None:
    """Parse arguments and run the pipeline for one gig, or all open gigs."""
    parser = argparse.ArgumentParser(
        description="Run the MatchScout recommender for a gig."
    )
    # Exactly one of --gig-id / --all is required.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gig-id", help="process a single gig by id")
    group.add_argument("--all", action="store_true",
                       help="process every open gig")
    args = parser.parse_args()

    # --- single gig ------------------------------------------------------
    if args.gig_id:
        recs = recommend_creators(args.gig_id)
        _print_recommendations(args.gig_id, recs)
        return

    # --- all open gigs ---------------------------------------------------
    open_gigs = db.list_gigs(status="open")
    if not open_gigs:
        print("No open gigs to process.")
        return

    print(f"Processing {len(open_gigs)} open gigs ...\n")
    total_cost = 0.0
    failures = 0
    for gig in open_gigs:
        # One gig failing (e.g. Arm 2 retries exhausted) shouldn't abort
        # the whole batch — catch, report, and keep going.
        try:
            recs = recommend_creators(gig.id)
            total_cost += sum(r.cost_usd for r in recs)
            arm = db.get_gig(gig.id).treatment_arm
            print(f"  {gig.id}: arm={arm}, {len(recs)} recs")
        except Exception as exc:
            failures += 1
            print(f"  {gig.id}: FAILED — {exc}")

    done = len(open_gigs) - failures
    print(f"\nDone. {done}/{len(open_gigs)} gigs processed "
          f"({failures} failed). Total LLM cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
