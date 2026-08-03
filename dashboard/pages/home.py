"""
dashboard/pages/home.py
========================
Home page — summary statistics and recent runs.

Loads all generated reports and displays:
- KPI metric cards (total, passed, failed, pass rate, avg duration)
- Recent runs table (last 10)
- Quick status breakdown chart
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.metrics_cards import render_summary_metrics
from dashboard.components.status_badge import render_status_badge
from dashboard.services.report_loader import ReportLoader


def render(report_dir: Path | None = None) -> None:
    """Render the Home page."""
    st.title("🏠 Agentic AI Test Automation")
    st.subheader("Dashboard Overview")

    loader = ReportLoader(report_dir)
    stats = loader.compute_stats()
    rows = loader.get_summary_rows()

    # ---------- KPI row ----------
    st.markdown("---")
    render_summary_metrics(stats)
    st.markdown("---")

    if not rows:
        st.info(
            "No test reports found yet.\n\n"
            "Run some tests to generate reports under `artifacts/reports/`."
        )
        return

    # ---------- Recent runs ----------
    st.subheader("Recent Runs")
    recent = rows[:10]
    df = pd.DataFrame(recent)

    display_cols = ["run_id", "status", "title", "generated_at"]
    for c in display_cols:
        if c not in df.columns:
            df[c] = ""

    st.dataframe(
        df[display_cols].rename(
            columns={
                "run_id": "Run ID",
                "status": "Status",
                "title": "Title",
                "generated_at": "Generated At",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ---------- Status breakdown ----------
    st.subheader("Status Breakdown")
    status_counts = {"Passed": stats["passed"], "Failed": stats["failed"], "Error": stats["error"]}
    chart_df = pd.DataFrame(
        {"Status": list(status_counts.keys()), "Count": list(status_counts.values())}
    ).set_index("Status")
    st.bar_chart(chart_df)
