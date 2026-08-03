"""
dashboard/pages/execution_history.py
======================================
Execution History page.

Full sortable/filterable table of all execution reports.
Users can click a run ID to drill into the Report Viewer.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard.components.report_table import render_report_table
from dashboard.services.report_loader import ReportLoader


def render(report_dir: Path | None = None) -> None:
    """Render the Execution History page."""
    st.title("📋 Execution History")
    st.caption("All execution runs, newest first.")

    loader = ReportLoader(report_dir)
    rows = loader.get_summary_rows()

    # Stats summary strip
    if rows:
        stats = loader.compute_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", stats["total"])
        c2.metric("Passed", stats["passed"])
        c3.metric("Failed", stats["failed"])
        c4.metric("Pass Rate", f"{stats['pass_rate']:.1f}%")
        st.markdown("---")

    render_report_table(rows, key="history")
