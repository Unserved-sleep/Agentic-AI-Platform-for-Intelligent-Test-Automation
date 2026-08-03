"""
dashboard/pages/analytics.py
==============================
Analytics page — charts and trends.

Visualises:
- Pass/fail trend over time (line chart)
- Status distribution (bar chart)
- Duration histogram
- Browser/environment breakdown
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.services.report_loader import ReportLoader


def render(report_dir: Path | None = None) -> None:
    """Render the Analytics page."""
    st.title("📊 Analytics")

    loader = ReportLoader(report_dir)
    rows = loader.get_summary_rows()
    stats = loader.compute_stats()

    if not rows:
        st.info("No reports found. Run some tests to generate analytics data.")
        return

    df = pd.DataFrame(rows)
    _ensure_columns(df)

    # ---- Top-level KPIs ----
    st.subheader("Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runs", stats["total"])
    c2.metric("Pass Rate", f"{stats['pass_rate']:.1f}%")
    c3.metric("Avg Duration", f"{stats['avg_duration_seconds']:.1f}s")
    c4.metric("Failed", stats["failed"])

    st.markdown("---")

    # ---- Status distribution ----
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Status Distribution")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = pd.Index(["Status", "Count"])
        st.bar_chart(status_counts.set_index("Status"))

    with col_right:
        st.subheader("Pass Rate by Browser")
        if "browser_type" in df.columns and df["browser_type"].notna().any():
            browser_df = df[df["browser_type"].notna() & (df["browser_type"] != "")]
            if not browser_df.empty:
                pivot = (
                    browser_df.groupby(["browser_type", "status"])
                    .size()
                    .unstack(fill_value=0)
                )
                st.bar_chart(pivot)
            else:
                st.info("No browser data available.")
        else:
            st.info("No browser data available.")

    st.markdown("---")

    # ---- Duration trend ----
    st.subheader("Duration Over Time")
    if "duration_seconds" in df.columns and "generated_at" in df.columns:
        dur_df = df[["generated_at", "duration_seconds", "status"]].copy()
        dur_df["duration_seconds"] = pd.to_numeric(dur_df["duration_seconds"], errors="coerce")
        dur_df = dur_df.dropna(subset=["duration_seconds"])
        dur_df = dur_df.sort_values("generated_at")

        if not dur_df.empty:
            st.line_chart(
                dur_df.set_index("generated_at")[["duration_seconds"]],
                use_container_width=True,
            )
        else:
            st.info("No duration data available.")
    else:
        st.info("Duration data not available.")

    # ---- Environment breakdown ----
    st.subheader("Runs by Environment")
    if "environment" in df.columns:
        env_df = df[df["environment"].notna() & (df["environment"] != "")]
        if not env_df.empty:
            env_counts = env_df["environment"].value_counts().reset_index()
            env_counts.columns = pd.Index(["Environment", "Count"])
            st.dataframe(env_counts, use_container_width=True, hide_index=True)
        else:
            st.info("No environment data tagged in reports.")

    # ---- Raw data table ----
    with st.expander("📋 Raw Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)


def _ensure_columns(df: pd.DataFrame) -> None:
    """Add missing columns with empty values."""
    for col in ["run_id", "status", "title", "generated_at",
                "duration_seconds", "environment", "browser_type"]:
        if col not in df.columns:
            df[col] = None
