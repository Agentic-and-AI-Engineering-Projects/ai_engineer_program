# ============================================================
# CHECKPOINT — Phase 1.5 Step 3A
# ============================================================
# Tomorrow: copy this entire file's contents into
# matchscout-onemyle/matchscout/db.py
#
# Then run: python -m matchscout.db  (from matchscout-onemyle/)
# Expected: "Schema ready at: .../data/matchscout.db" with 0 gigs
# ============================================================

"""
SQLite layer for MatchScout — gigs + recommendations.

One unified `gigs` table with a `status` field tracks the full lifecycle.
Historical gigs (loaded from matches.csv) and newly posted gigs both live
here; the only difference is `status`.

All list-typed fields are stored as JSON strings in TEXT columns —
SQLite has no native list/dict type. Conversion happens at the boundary
via _gig_to_row / _row_to_gig.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from matchscout.schemas import Gig, CreatorRecommendation


DB_PATH = Path(__file__).parent.parent / "data" / "matchscout.db"


# ============================================================
# Connection + schema
# ============================================================

def get_conn() -> sqlite3.Connection:
    """Open a SQLite connection with row-as-dict factory + FK enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema() -> None:
    """Create tables + indexes if they don't exist. Idempotent."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS gigs (
            id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            posted_at TEXT NOT NULL,
            status TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategories TEXT NOT NULL,        -- JSON list
            content_needs TEXT NOT NULL,        -- JSON list
            budget_range TEXT NOT NULL,         -- JSON [low, high]
            timeline_days INTEGER NOT NULL,
            location_required TEXT NOT NULL,
            remote_acceptable INTEGER NOT NULL, -- 0 or 1
            niche_tags TEXT NOT NULL,           -- JSON list
            treatment_arm TEXT,
            assigned_creator_id TEXT,
            outcome TEXT,
            business_rating REAL,
            creator_rating REAL,
            completed_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_gigs_status   ON gigs(status);
        CREATE INDEX IF NOT EXISTS idx_gigs_business ON gigs(business_id);
        CREATE INDEX IF NOT EXISTS idx_gigs_creator  ON gigs(assigned_creator_id);

        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            gig_id TEXT NOT NULL,
            creator_id TEXT NOT NULL,
            rank INTEGER NOT NULL,
            source_arm TEXT NOT NULL,
            prompt_version TEXT,
            reasoning TEXT,
            strengths TEXT NOT NULL DEFAULT '[]',
            risks TEXT NOT NULL DEFAULT '[]',
            key_signals TEXT NOT NULL DEFAULT '[]',
            generated_at TEXT NOT NULL,
            cost_usd REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (gig_id) REFERENCES gigs(id)
        );

        CREATE INDEX IF NOT EXISTS idx_recs_gig ON recommendations(gig_id);
    """)
    conn.commit()
    conn.close()


# ============================================================
# Pydantic <-> row conversion
# ============================================================

def _gig_to_row(g: Gig) -> dict:
    """Pydantic Gig -> dict of column values, ready for INSERT."""
    return {
        "id": g.id,
        "business_id": g.business_id,
        "posted_at": g.posted_at.isoformat(),
        "status": g.status,
        "category": g.category,
        "subcategories": json.dumps(g.subcategories),
        "content_needs": json.dumps(g.content_needs),
        "budget_range": json.dumps(g.budget_range),
        "timeline_days": g.timeline_days,
        "location_required": g.location_required,
        "remote_acceptable": int(g.remote_acceptable),
        "niche_tags": json.dumps(g.niche_tags),
        "treatment_arm": g.treatment_arm,
        "assigned_creator_id": g.assigned_creator_id,
        "outcome": g.outcome,
        "business_rating": g.business_rating,
        "creator_rating": g.creator_rating,
        "completed_at": g.completed_at.isoformat() if g.completed_at else None,
    }


def _row_to_gig(row: sqlite3.Row) -> Gig:
    """SQLite row -> typed Pydantic Gig."""
    return Gig(
        id=row["id"],
        business_id=row["business_id"],
        posted_at=datetime.fromisoformat(row["posted_at"]),
        status=row["status"],
        category=row["category"],
        subcategories=json.loads(row["subcategories"]),
        content_needs=json.loads(row["content_needs"]),
        budget_range=json.loads(row["budget_range"]),
        timeline_days=row["timeline_days"],
        location_required=row["location_required"],
        remote_acceptable=bool(row["remote_acceptable"]),
        niche_tags=json.loads(row["niche_tags"]),
        treatment_arm=row["treatment_arm"],
        assigned_creator_id=row["assigned_creator_id"],
        outcome=row["outcome"],
        business_rating=row["business_rating"],
        creator_rating=row["creator_rating"],
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
    )


def _rec_to_row(r: CreatorRecommendation) -> dict:
    return {
        "id": r.id,
        "gig_id": r.gig_id,
        "creator_id": r.creator_id,
        "rank": r.rank,
        "source_arm": r.source_arm,
        "prompt_version": r.prompt_version,
        "reasoning": r.reasoning,
        "strengths": json.dumps(r.strengths),
        "risks": json.dumps(r.risks),
        "key_signals": json.dumps(r.key_signals),
        "generated_at": r.generated_at.isoformat(),
        "cost_usd": r.cost_usd,
    }


# ============================================================
# Gig CRUD
# ============================================================

def insert_gigs(gigs: list[Gig]) -> None:
    """Bulk insert. Raises sqlite3.IntegrityError if any id already exists."""
    conn = get_conn()
    try:
        for gig in gigs:
            row = _gig_to_row(gig)
            cols = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row.keys())
            conn.execute(f"INSERT INTO gigs ({cols}) VALUES ({placeholders})", row)
        conn.commit()
    finally:
        conn.close()


def get_gig(gig_id: str) -> Optional[Gig]:
    """Fetch one gig by id. None if not found."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM gigs WHERE id = ?", (gig_id,)).fetchone()
        return _row_to_gig(row) if row else None
    finally:
        conn.close()


def list_gigs(status: Optional[str] = None) -> list[Gig]:
    """List all gigs, optionally filtered by status."""
    conn = get_conn()
    try:
        if status:
            rows = conn.execute("SELECT * FROM gigs WHERE status = ?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM gigs").fetchall()
        return [_row_to_gig(r) for r in rows]
    finally:
        conn.close()


def recent_completed_gigs_for_creator(creator_id: str, limit: int = 10) -> list[Gig]:
    """Last N completed/failed gigs for a creator. Used by Stage 3 LLM (Arm 2)."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT * FROM gigs
            WHERE assigned_creator_id = ?
              AND status IN ('completed', 'failed')
            ORDER BY completed_at DESC
            LIMIT ?
        """, (creator_id, limit)).fetchall()
        return [_row_to_gig(r) for r in rows]
    finally:
        conn.close()


def recent_completed_gigs_for_business(business_id: str, limit: int = 10) -> list[Gig]:
    """Last N completed/failed gigs for a business."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT * FROM gigs
            WHERE business_id = ?
              AND status IN ('completed', 'failed')
            ORDER BY completed_at DESC
            LIMIT ?
        """, (business_id, limit)).fetchall()
        return [_row_to_gig(r) for r in rows]
    finally:
        conn.close()


# ============================================================
# Recommendations CRUD
# ============================================================

def insert_recommendations(recs: list[CreatorRecommendation]) -> None:
    """Bulk insert recommendations for a gig."""
    conn = get_conn()
    try:
        for r in recs:
            row = _rec_to_row(r)
            cols = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row.keys())
            conn.execute(f"INSERT INTO recommendations ({cols}) VALUES ({placeholders})", row)
        conn.commit()
    finally:
        conn.close()

def update_gig(gig_id: str, **fields) -> None:
    """Update one or more columns of a gig row.

    Pass column=value keyword pairs, e.g.:
        update_gig("gig_open_001", treatment_arm="llm", status="in_review")

    datetime values are converted to ISO strings (SQLite stores them as
    TEXT). List-typed columns are not supported here — only the scalar
    lifecycle fields (treatment_arm, status, assigned_creator_id, outcome,
    ratings, completed_at) are ever updated this way.
    """
    # Nothing to do if no fields were passed.
    if not fields:
        return

    # Convert any datetime values to ISO strings for SQLite storage.
    clean = {}
    for key, value in fields.items():
        clean[key] = value.isoformat() if isinstance(value, datetime) else value

    # Build the "col = :col" assignment list for the UPDATE statement.
    assignments = ", ".join(f"{col} = :{col}" for col in clean)
    clean["_gig_id"] = gig_id   # bind value for the WHERE clause

    conn = get_conn()
    try:
        conn.execute(
            f"UPDATE gigs SET {assignments} WHERE id = :_gig_id", clean
        )
        conn.commit()
    finally:
        conn.close()


# ============================================================
# Smoke test entry
# ============================================================

if __name__ == "__main__":
    init_schema()
    n_gigs = len(list_gigs())
    n_open = len(list_gigs(status="open"))
    n_completed = len(list_gigs(status="completed"))
    print(f"Schema ready at: {DB_PATH}")
    print(f"  Total gigs: {n_gigs}")
    print(f"  Open gigs: {n_open}")
    print(f"  Completed gigs: {n_completed}")
