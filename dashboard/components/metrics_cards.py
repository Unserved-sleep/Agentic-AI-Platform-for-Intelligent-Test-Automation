"""
dashboard/components/metrics_cards.py
=======================================
Summary metric card components for the Home and Analytics pages.

Renders a row of ``st.metric`` tiles from a stats dict produced
by ``ReportLoader.compute_stats()``.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_summary_metrics(stats: dict[str, Any]) -> None:
    """
    Render a top-level metrics row.

    Parameters
    ----------
    stats:
        Dict from ``ReportLoader.compute_stats()``.
        Expected keys: total, passed, failed, error, pass_rate,
        avg_duration_seconds.
    """
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Runs", stats.get("total", 0))
    with col2:
        st.metric(
            "Passed",
            stats.get("passed", 0),
            delta=None,
            delta_color="normal",
        )
    with col3:
        st.metric(
            "Failed",
            stats.get("failed", 0),
            delta=None,
        )
    with col4:
        st.metric("Errors", stats.get("error", 0))
    with col5:
        st.metric(
            "Pass Rate",
            f"{stats.get('pass_rate', 0.0):.1f}%",
        )
    with col6:
        avg = stats.get("avg_duration_seconds", 0.0)
        st.metric("Avg Duration", f"{avg:.1f}s")


def render_single_report_metrics(report: dict[str, Any]) -> None:
    """
    Render metric tiles for a single report detail view.

    Parameters
    ----------
    report:
        Parsed report dict from ReportLoader.
    """
    # Extract summary section if available
    summary_data: dict[str, Any] = {}
    for section in report.get("sections", []):
        if section.get("section_type") == "summary":
            summary_data = section.get("data", {})
            break

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", report.get("status", "—"))
    with col2:
        duration = summary_data.get("duration_seconds", 0.0)
        st.metric("Duration", f"{duration:.2f}s")
    with col3:
        st.metric("Environment", summary_data.get("environment", "—") or "—")
    with col4:
        st.metric("Browser", summary_data.get("browser_type", "—") or "—")
