

"""
pipeline.py — the MatchScout orchestrator, as a single LangGraph state machine.

The whole pipeline is one graph:

  stage1 -> stage2 -> arm_decider
       arm_decider --(10%)--> arm1 --------------------------+
       arm_decider --(90%)--> arm2_metrics -> arm2_call ->   |
                                  arm2_validate              |
                                    --(retry)--> arm2_call   |
                                    --(ok)-----> arm2_assemble
                                    --(giveup)-> END         |
                              arm2_assemble -----------------+
                                                             |
                              persist_recommendations <------+
                                     -> END

Every stage is a node; the arm decision and the retry loop are conditional
edges. recommend_creators(gig_id) builds the initial state and invokes it.
"""

import random
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from matchscout import db
from matchscout.schemas import Gig, CreatorRecommendation
from matchscout.data_loader import load_creators
from matchscout.filter import filter_candidates
from matchscout.ranker import rank_candidates
from matchscout.agent import (
    compute_candidate_metrics,
    build_prompt,
    call_llm,
    validate_llm_response,
    assemble_recommendations,
    build_no_llm_recommendations,
)

# Fraction of gigs routed to the no-LLM control arm — the A/B coin flip.
CONTROL_FRACTION = 0.10
# How many times Arm 2 will re-call the LLM if validation fails.
MAX_LLM_ATTEMPTS = 3

# ============================================================
# Graph state
# ============================================================

class PipelineState(TypedDict):
    """State threaded through the whole pipeline graph. Each node reads the
    fields it needs and returns a partial dict that LangGraph merges back in."""
    gig: Gig
    creators: dict                # dict[str, Creator] — the full catalog
    candidates: list              # list[Creator] — Stage 1 survivors
    ranked: list                  # list[(Creator, float)] — Stage 2 top 10
    arm: str                      # "no_llm" | "llm"
    metrics: list                 # list[CandidateMetrics] — Arm 2 only
    llm_response: object          # _LLMResponse | None — Arm 2 only
    cost: float                   # accumulated LLM cost for this gig
    attempts: int                 # Arm 2 LLM call attempts so far
    error: Optional[str]          # set when a step fails
    recommendations: list         # list[CreatorRecommendation] — final output

# ============================================================
# Nodes — each is a thin wrapper around a stage function
# ============================================================

def _node_stage1(state: PipelineState) -> dict:
    """Stage 1 — hard-filter the creator catalog down to viable candidates."""
    candidates = filter_candidates(state["gig"], state["creators"])
    return {"candidates": candidates}

def _node_stage2(state: PipelineState) -> dict:
    """Stage 2 — rank the candidates by vector similarity; keep the top 10."""
    ranked = rank_candidates(state["gig"], state["candidates"], top_k=10)
    return {"ranked": ranked}

def _node_arm_decider(state: PipelineState) -> dict:
    """Flip the A/B coin — 10% of gigs go to the no-LLM control arm."""
    arm = "no_llm" if random.random() < CONTROL_FRACTION else "llm"
    return {"arm": arm}

def _node_arm1(state: PipelineState) -> dict:
    """Arm 1 — no LLM. Take the top 3 candidates by cosine score."""
    recs = build_no_llm_recommendations(state["gig"], state["ranked"])
    return {"recommendations": recs}

def _node_arm2_metrics(state: PipelineState) -> dict:
    """Arm 2 — compute each candidate's past-gig metrics for the LLM."""
    metrics = compute_candidate_metrics(state["ranked"])
    return {"metrics": metrics}

def _node_arm2_call(state: PipelineState) -> dict:
    """Arm 2 — build the prompt and call Claude. On failure, record the
    error so the validate node can route to a retry."""
    attempt = state["attempts"] + 1
    try:
        parsed, call_cost = call_llm(build_prompt(state["gig"], state["metrics"]))
        return {
            "llm_response": parsed,
            "cost": state["cost"] + call_cost,
            "attempts": attempt,
            "error": None,
        }
    except Exception as exc:
        return {"llm_response": None, "attempts": attempt, "error": str(exc)}

def _node_arm2_validate(state: PipelineState) -> dict:
    """Arm 2 — validate the LLM response. Sets 'error' if it's unusable."""
    # If the call itself failed, leave that error in place — nothing to check.
    if state["error"]:
        return {}
    err = validate_llm_response(state["llm_response"], state["metrics"])
    return {"error": err}

def _node_arm2_assemble(state: PipelineState) -> dict:
    """Arm 2 — turn the validated LLM response into recommendation rows."""
    recs = assemble_recommendations(
        state["gig"], state["llm_response"], state["cost"]
    )
    return {"recommendations": recs}

def _node_persist_recommendations(state: PipelineState) -> dict:
    """Write the 3 recommendations to SQLite and advance the gig to
    'in_review' (recommendations ready, business hasn't picked yet)."""
    db.update_gig(
        state["gig"].id, treatment_arm=state["arm"], status="in_review"
    )
    db.insert_recommendations(state["recommendations"])
    return {}

# ============================================================
# Routers — the conditional edges
# ============================================================

def _route_arm(state: PipelineState) -> str:
    """After arm_decider: route to the chosen arm."""
    return state["arm"]   # "no_llm" or "llm"

def _route_after_validate(state: PipelineState) -> str:
    """After arm2_validate: ok -> assemble; error with retries left -> retry;
    error with attempts exhausted -> giveup."""
    if not state["error"]:
        return "ok"
    if state["attempts"] < MAX_LLM_ATTEMPTS:
        return "retry"
    return "giveup"

# ============================================================
# Build + compile the graph (once, at import time)
# ============================================================

def _build_pipeline_graph():
    """Wire the nodes and edges into the compiled pipeline graph."""
    g = StateGraph(PipelineState)

    # Register every stage as a node.
    g.add_node("stage1", _node_stage1)
    g.add_node("stage2", _node_stage2)
    g.add_node("arm_decider", _node_arm_decider)
    g.add_node("arm1", _node_arm1)
    g.add_node("arm2_metrics", _node_arm2_metrics)
    g.add_node("arm2_call", _node_arm2_call)
    g.add_node("arm2_validate", _node_arm2_validate)
    g.add_node("arm2_assemble", _node_arm2_assemble)
    g.add_node("persist_recommendations", _node_persist_recommendations)

    # Linear lead-in: filter -> rank -> decide arm.
    g.set_entry_point("stage1")
    g.add_edge("stage1", "stage2")
    g.add_edge("stage2", "arm_decider")

    # Branch on the treatment arm.
    g.add_conditional_edges(
        "arm_decider", _route_arm,
        {"no_llm": "arm1", "llm": "arm2_metrics"},
    )

    # Arm 1 path.
    g.add_edge("arm1", "persist_recommendations")

    # Arm 2 path, with the validate -> retry loop.
    g.add_edge("arm2_metrics", "arm2_call")
    g.add_edge("arm2_call", "arm2_validate")
    g.add_conditional_edges(
        "arm2_validate", _route_after_validate,
        {"ok": "arm2_assemble", "retry": "arm2_call", "giveup": END},
    )
    g.add_edge("arm2_assemble", "persist_recommendations")

    # Both arms converge here, then finish.
    g.add_edge("persist_recommendations", END)

    return g.compile()

# Compile once at import — reused for every gig.
_PIPELINE_GRAPH = _build_pipeline_graph()

# ============================================================
# Public entry point
# ============================================================

def recommend_creators(gig_id: str) -> list[CreatorRecommendation]:
    """Run the full pipeline graph for one gig and persist its recommendations.

    Loads the gig, builds the initial state, invokes the graph, and returns
    the recommendations. Raises if the gig isn't found, isn't 'open', or the
    graph finished without producing recommendations (Arm 2 retries exhausted).
    """
    # Load the gig and confirm it's fresh.
    gig = db.get_gig(gig_id)
    if gig is None:
        raise ValueError(f"gig not found: {gig_id}")
    if gig.status != "open":
        raise ValueError(
            f"gig {gig_id} has status '{gig.status}', expected 'open' "
            f"(already processed?)"
        )

    # Build the initial state — every PipelineState key gets a starting value.
    initial: PipelineState = {
        "gig": gig,
        "creators": load_creators(),
        "candidates": [],
        "ranked": [],
        "arm": "",
        "metrics": [],
        "llm_response": None,
        "cost": 0.0,
        "attempts": 0,
        "error": None,
        "recommendations": [],
    }

    # Run the graph end-to-end.
    final = _PIPELINE_GRAPH.invoke(initial)

    # If Arm 2 exhausted its retries, the graph reaches END with no recs.
    if not final["recommendations"]:
        raise RuntimeError(
            f"pipeline produced no recommendations for {gig_id} "
            f"(arm={final['arm']}, error={final['error']})"
        )

    return final["recommendations"]

# ---------- smoke test ----------

if __name__ == "__main__":
    # Process one open gig end-to-end and show what got written.
    open_gigs = db.list_gigs(status="open")
    if not open_gigs:
        print("No open gigs left — re-seed the DB to get fresh ones.")
        raise SystemExit

    gig = open_gigs[0]
    print(f"Running pipeline for {gig.id} "
          f"({gig.category}, {gig.location_required}) ...\n")

    recs = recommend_creators(gig.id)
    arm = db.get_gig(gig.id).treatment_arm

    print(f"Treatment arm: {arm}  —  {len(recs)} recommendations written:\n")
    for rec in recs:
        print(f"  rank {rec.rank}: {rec.creator_id}  (${rec.cost_usd:.4f})")
        if rec.reasoning:
            print(f"    {rec.reasoning[:110]}...")

    remaining = len(db.list_gigs(status="open"))
    print(f"\n{gig.id} is now 'in_review'. {remaining} open gigs remain.")
