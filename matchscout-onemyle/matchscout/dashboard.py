"""
dashboard.py — Streamlit two-arm outcome dashboard for MatchScout.

Shows headline metrics, chi-squared significance, bar chart, and
a gig-level drill-down table. Reads directly from SQLite.

Run:  streamlit run matchscout/dashboard.py
"""

import os
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "matchscout.db")

@st.cache_data
def load_summary() -> pd.DataFrame:
    """Load all summary_stats rows, most recent first."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM summary_stats ORDER BY run_at DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data
def load_gigs() -> pd.DataFrame:
    """Load completed/failed gigs joined with their rank-1 recommendation."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT g.id,
               g.treatment_arm,
               g.outcome,
               g.business_rating,
               g.assigned_creator_id,
               r1.creator_id    AS rank1_creator,
               r1.prompt_version
        FROM   gigs g
        JOIN   recommendations r1
               ON r1.gig_id = g.id AND r1.rank = 1
        WHERE  g.status IN ('completed', 'failed')
          AND  g.treatment_arm IS NOT NULL
        """,
        conn,
    )
    conn.close()
    return df

if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

summary_df = load_summary()

if summary_df.empty:
    st.warning("No summary stats found — run `python -m matchscout.dashboard_batch` first.")
    st.stop()

# Isolate the most recent batch run.
latest_run = summary_df["run_at"].max()
latest     = summary_df[summary_df["run_at"] == latest_run]

llm_row  = latest[latest["arm"] == "llm"].iloc[0]   if "llm"    in latest["arm"].values else None
ctrl_row = latest[latest["arm"] == "no_llm"].iloc[0] if "no_llm" in latest["arm"].values else None

st.subheader("Headline Metrics")
c1, c2, c3, c4 = st.columns(4)

if llm_row is not None and ctrl_row is not None:
    c1.metric(
        "Success Rate — LLM",
        f"{llm_row['gig_success_rate']:.1%}",
        delta=f"{llm_row['gig_success_rate'] - ctrl_row['gig_success_rate']:+.1%} vs baseline",
    )
    c2.metric("Success Rate — No-LLM", f"{ctrl_row['gig_success_rate']:.1%}")
    c3.metric(
        "Avg Rating — LLM",
        f"{llm_row['avg_rating']:.2f}",
        delta=f"{llm_row['avg_rating'] - ctrl_row['avg_rating']:+.2f} vs baseline",
    )
    c4.metric("Avg Rating — No-LLM", f"{ctrl_row['avg_rating']:.2f}")

st.subheader("Statistical Significance")
p_val = latest["chi2_p_value"].iloc[0]

if pd.notna(p_val):
    if p_val < 0.05:
        st.success(f"SIGNIFICANT — p = {p_val:.4f}  (< 0.05). LLM arm is outperforming.")
    else:
        st.warning(f"Not significant yet — p = {p_val:.4f}.  Need more gigs to confirm.")


st.subheader("Success Rate by Arm")

if llm_row is not None and ctrl_row is not None:
    chart_df = pd.DataFrame({
        "Arm":          ["LLM (arm2)", "No-LLM (arm1)"],
        "Success Rate": [llm_row["gig_success_rate"], ctrl_row["gig_success_rate"]],
    }).set_index("Arm")
    st.bar_chart(chart_df)

st.subheader("By Prompt Version")
st.dataframe(
    latest[[
        "arm", "n", "top_1_selection_rate", "gig_success_rate",
        "composite_good_outcome_rate", "avg_rating", "prompt_version",
    ]],
    use_container_width=True,
)
st.subheader("Gig-Level Drill-Down")

gigs_df    = load_gigs()
arm_filter = st.selectbox("Filter by arm", ["all", "llm", "no_llm"])

if arm_filter != "all":
    gigs_df = gigs_df[gigs_df["treatment_arm"] == arm_filter]

st.dataframe(gigs_df, use_container_width=True)
