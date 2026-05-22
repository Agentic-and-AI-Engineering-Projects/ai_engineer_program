"""
dashboard_batch.py — Phase 4 outcome aggregator for MatchScout.

Two responsibilities:
  1. simulate_outcomes() — for each in_review gig, synthesise which creator
     the business accepted and whether the gig succeeded. Writes results back
     to SQLite. Idempotent: skips gigs already past in_review.

  2. compute_metrics() — aggregate per (treatment_arm, prompt_version):
       top_1_selection_rate, gig_success_rate, composite_good_outcome_rate,
       avg_rating. Runs chi-squared between arms.

  3. write_results() — appends a summary_stats row per arm to SQLite.

Run standalone:  python -m matchscout.dashboard_batch
"""

import hashlib
import os
import random
import sqlite3
from datetime import datetime, timezone

# Default path: matchscout/ -> data/matchscout.db
_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "matchscout.db")

def _creator_reliability(creator_id: str) -> float:
    """Deterministic score in [0.15, 0.95] derived from the creator id hash.

    Identical to seed_db._creator_reliability — do not change the formula
    without updating both files.
    """
    digest = int(hashlib.md5(creator_id.encode()).hexdigest(), 16)
    return 0.15 + (digest % 1000) / 1000 * 0.80

# Probability mass for the business choosing rank 1, 2, or 3.
_RANK_WEIGHTS = [0.60, 0.27, 0.13]


def _simulate_one_gig(gig_id: str, recs: list[tuple]) -> dict:
    """Synthesise the business decision for one gig.

    recs: [(creator_id, rank), ...] — the 3 recommendations for this gig.
    Returns a dict with keys ready to UPDATE the gigs row.

    Seeded by gig_id so re-running produces the same result.
    """
    # Seed by gig_id so the simulation is reproducible across runs.
    rng = random.Random(gig_id)

    # Sort by rank (1, 2, 3) and extract just the creator ids in that order.
    ordered = [cid for cid, _ in sorted(recs, key=lambda x: x[1])]

    # Business picks one creator, weighted toward rank 1.
    chosen_creator = rng.choices(ordered, weights=_RANK_WEIGHTS)[0]

    # Flip the success coin using the creator's hidden reliability score.
    r = _creator_reliability(chosen_creator)
    p_success = 0.30 + 0.65 * r
    success = rng.random() < p_success

    # Generate a business rating (1–5). Failed gigs pull the rating down.
    raw = 2.0 + 3.0 * r + rng.uniform(-0.5, 0.5)
    if not success:
        raw -= 1.5
    rating = round(max(1.0, min(5.0, raw)), 1)

    return {
        "assigned_creator_id": chosen_creator,
        "outcome":             "success" if success else "failed",
        "business_rating":     rating,
        "status":              "completed" if success else "failed",
        "completed_at":        datetime.now(timezone.utc).isoformat(),
    }
def simulate_outcomes(db_path: str = _DEFAULT_DB) -> int:
    """Simulate business decisions for all in_review gigs and write results back.

    Idempotent: only touches gigs with status = 'in_review'.
    Returns the count of gigs simulated.
    """
    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()

        # Fetch only gigs that haven't been processed yet.
        c.execute("SELECT id FROM gigs WHERE status = 'in_review'")
        gig_ids = [row[0] for row in c.fetchall()]

        for gig_id in gig_ids:
            # Get the 3 recommendations for this gig.
            c.execute(
                "SELECT creator_id, rank FROM recommendations WHERE gig_id = ?",
                (gig_id,),
            )
            recs = c.fetchall()
            if not recs:
                continue

            sim = _simulate_one_gig(gig_id, recs)

            c.execute(
                """
                UPDATE gigs
                SET assigned_creator_id = :assigned_creator_id,
                    outcome             = :outcome,
                    business_rating     = :business_rating,
                    status              = :status,
                    completed_at        = :completed_at
                WHERE id = :gig_id
                """,
                {**sim, "gig_id": gig_id},
            )

        conn.commit()
        return len(gig_ids)
    finally:
        conn.close()

def compute_metrics(db_path: str = _DEFAULT_DB) -> dict:
    """Aggregate per-arm outcome metrics and run chi-squared significance test.

    Metrics per arm:
      top_1_selection_rate       — fraction where business chose rank 1
      gig_success_rate           — fraction of gigs that succeeded
      composite_good_outcome_rate — rank 1 chosen AND success AND rating >= 4.0
      avg_rating                 — mean business rating (1–5)

    Returns:
      {
        "by_arm": { arm: { n, top_1_selection_rate, gig_success_rate,
                           composite_good_outcome_rate, avg_rating,
                           prompt_version } },
        "chi_squared": { chi2, p_value, dof } | None,
      }
    """
    from scipy.stats import chi2_contingency

    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()
        # One row per gig: gig fields + the rank-1 recommendation creator.
        c.execute(
            """
            SELECT g.id,
                   g.treatment_arm,
                   g.assigned_creator_id,
                   g.outcome,
                   g.business_rating,
                   r1.creator_id    AS rank1_creator,
                   r1.prompt_version
            FROM   gigs g
            JOIN   recommendations r1
                   ON r1.gig_id = g.id AND r1.rank = 1
            WHERE  g.status IN ('completed', 'failed')
              AND  g.treatment_arm IS NOT NULL
            """
        )
        rows = c.fetchall()
    finally:
        conn.close()

    # Accumulate raw counts per arm.
    arms: dict = {}
    for _, arm, assigned, outcome, rating, rank1_creator, prompt_ver in rows:
        if arm not in arms:
            arms[arm] = {
                "total": 0, "top1_selected": 0, "success": 0,
                "composite_good": 0, "ratings": [],
                "prompt_version": prompt_ver or "none",
            }
        a = arms[arm]
        a["total"] += 1
        top1_chosen = assigned == rank1_creator
        succeeded   = outcome == "success"
        if top1_chosen:
            a["top1_selected"] += 1
        if succeeded:
            a["success"] += 1
        if top1_chosen and succeeded and (rating or 0.0) >= 4.0:
            a["composite_good"] += 1
        if rating is not None:
            a["ratings"].append(rating)

    # Convert raw counts to rates.
    by_arm: dict = {}
    for arm, a in arms.items():
        n = a["total"]
        by_arm[arm] = {
            "n":                           n,
            "top_1_selection_rate":        round(a["top1_selected"] / n, 4),
            "gig_success_rate":            round(a["success"]       / n, 4),
            "composite_good_outcome_rate": round(a["composite_good"] / n, 4),
            "avg_rating":                  round(
                sum(a["ratings"]) / len(a["ratings"]) if a["ratings"] else 0.0, 3
            ),
            "prompt_version": a["prompt_version"],
        }

    # Chi-squared on success / fail counts between the two arms.
    chi2_result = None
    if "llm" in arms and "no_llm" in arms:
        llm  = arms["llm"]
        ctrl = arms["no_llm"]
        contingency = [
            [llm["success"],  llm["total"]  - llm["success"]],
            [ctrl["success"], ctrl["total"] - ctrl["success"]],
        ]
        chi2, p_val, dof, _ = chi2_contingency(contingency, correction=False)
        chi2_result = {
            "chi2":    round(chi2, 4),
            "p_value": round(p_val, 4),
            "dof":     dof,
        }

    return {"by_arm": by_arm, "chi_squared": chi2_result}
def write_results(metrics: dict, db_path: str = _DEFAULT_DB) -> None:
    """Append one summary_stats row per arm from the latest metrics run."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summary_stats (
                run_at                      TEXT,
                arm                         TEXT,
                n                           INTEGER,
                top_1_selection_rate        REAL,
                gig_success_rate            REAL,
                composite_good_outcome_rate REAL,
                avg_rating                  REAL,
                prompt_version              TEXT,
                chi2_p_value                REAL
            )
            """
        )
        run_at = datetime.now(timezone.utc).isoformat()
        chi_p  = (metrics["chi_squared"] or {}).get("p_value")

        for arm, m in metrics["by_arm"].items():
            conn.execute(
                "INSERT INTO summary_stats VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    run_at, arm, m["n"],
                    m["top_1_selection_rate"],
                    m["gig_success_rate"],
                    m["composite_good_outcome_rate"],
                    m["avg_rating"],
                    m["prompt_version"],
                    chi_p,
                ),
            )
        conn.commit()
    finally:
        conn.close()
if __name__ == "__main__":
    db_path = _DEFAULT_DB

    print("Step 1 — simulating outcomes for in_review gigs …")
    n = simulate_outcomes(db_path)
    print(f"         Simulated {n} gigs.\n")

    print("Step 2 — computing per-arm metrics …")
    metrics = compute_metrics(db_path)

    print("\n── Per-arm results ───────────────────────────────────────────────")
    for arm, m in metrics["by_arm"].items():
        print(f"\n  Arm: {arm!r}   n={m['n']}   prompt={m['prompt_version']}")
        print(f"    Top-1 selection rate:          {m['top_1_selection_rate']:.1%}")
        print(f"    Gig success rate:              {m['gig_success_rate']:.1%}")
        print(f"    Composite good outcome rate:   {m['composite_good_outcome_rate']:.1%}")
        print(f"    Avg business rating:           {m['avg_rating']:.2f} / 5.0")

    chi = metrics["chi_squared"]
    if chi:
        sig = "SIGNIFICANT (p < 0.05)" if chi["p_value"] < 0.05 else "not significant yet"
        print(f"\n── Chi-squared (success, llm vs no_llm) ─────────────────────────")
        print(f"  χ² = {chi['chi2']}   p = {chi['p_value']}   dof = {chi['dof']}")
        print(f"  Verdict: {sig}")

    print("\nStep 3 — writing summary_stats table …")
    write_results(metrics, db_path)
    print("         Done.")
    print("\n  To inspect: SELECT * FROM summary_stats ORDER BY run_at DESC LIMIT 10;")
