"""
dashboard/pages/report_viewer.py
===================================
Report Viewer page — per-report detail view.

Lets the user pick a run from a selectbox, then displays:
- Status badge + metric tiles
- Each report section (summary, artifacts, console logs, network,
  browser state, DOM, error) in expandable panels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.metrics_cards import render_single_report_metrics
from dashboard.components.report_table import render_run_selector
from dashboard.components.status_badge import render_status_badge
from dashboard.services.report_loader import ReportLoader


def render(report_dir: Path | None = None) -> None:
    """Render the Report Viewer page."""
    st.title("🔍 Report Viewer")

    loader = ReportLoader(report_dir)
    rows = loader.get_summary_rows()

    run_id = render_run_selector(rows, key="viewer_run_selector")
    if not run_id:
        return

    report = loader.load_report(run_id)
    if report is None:
        st.error(f"Could not load report for run: {run_id}")
        return

    # Header
    st.markdown("---")
    col_title, col_badge = st.columns([4, 1])
    with col_title:
        st.subheader(report.get("title", "Execution Report"))
        st.caption(f"Run ID: `{report.get('run_id', run_id)}`  |  Generated: {report.get('generated_at', '')[:19]}")
    with col_badge:
        render_status_badge(report.get("status", "UNKNOWN"))

    st.markdown("---")
    render_single_report_metrics(report)
    st.markdown("---")

    # Sections
    for section in report.get("sections", []):
        _render_section(section)


def _render_section(section: dict[str, Any]) -> None:
    """Render a single report section in an expander."""
    title = section.get("title", "Section")
    stype = section.get("section_type", "")
    data = section.get("data", {})

    with st.expander(f"**{title}**", expanded=(stype == "summary")):
        if stype == "summary":
            _render_summary(data)
        elif stype == "artifacts":
            _render_artifacts(data)
        elif stype == "console_logs":
            _render_console_logs(data)
        elif stype == "network":
            _render_network(data)
        elif stype == "browser_state":
            _render_browser_state(data)
        elif stype == "dom":
            _render_dom(data)
        elif stype == "error":
            _render_error(data)
        else:
            st.json(data)


def _render_summary(data: dict[str, Any]) -> None:
    cols = st.columns(4)
    fields = [
        ("Run ID", "run_id"),
        ("Status", "status"),
        ("Started", "started_at"),
        ("Completed", "completed_at"),
        ("Duration", "duration_seconds"),
        ("Environment", "environment"),
        ("Browser", "browser_type"),
    ]
    for i, (label, key) in enumerate(fields):
        val = data.get(key, "—")
        if key == "duration_seconds":
            val = f"{float(val):.2f}s" if val not in ("", None, "—") else "—"
        cols[i % 4].markdown(f"**{label}:** {val}")


def _render_artifacts(data: dict[str, Any]) -> None:
    for group in ("screenshots", "traces", "videos", "logs"):
        entries = data.get(group, [])
        if entries:
            st.markdown(f"**{group.capitalize()}** ({len(entries)})")
            df = pd.DataFrame(entries)
            st.dataframe(df, use_container_width=True, hide_index=True)


def _render_console_logs(data: dict[str, Any]) -> None:
    entries = data.get("entries", [])
    if not entries:
        st.info("No console log entries.")
        return
    df = pd.DataFrame(entries)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(entries)} log entries")


def _render_network(data: dict[str, Any]) -> None:
    for group in ("requests", "responses", "failures"):
        items = data.get(group, [])
        if items:
            st.markdown(f"**{group.capitalize()}** ({len(items)})")
            st.dataframe(
                pd.DataFrame(items),
                use_container_width=True,
                hide_index=True,
            )


def _render_browser_state(data: dict[str, Any]) -> None:
    fields = [
        ("URL", "current_url"),
        ("Title", "title"),
        ("User Agent", "user_agent"),
        ("Viewport", None),
        ("Cookies", "cookie_count"),
    ]
    for label, key in fields:
        if key == "Viewport" or key is None:
            w = data.get("viewport_width", "?")
            h = data.get("viewport_height", "?")
            st.markdown(f"**Viewport:** {w} × {h}")
        else:
            st.markdown(f"**{label}:** {data.get(key, '—')}")


def _render_dom(data: dict[str, Any]) -> None:
    st.markdown(f"**URL:** {data.get('url', '—')}")
    st.markdown(f"**HTML size:** {data.get('html_size_bytes', 0):,} bytes")
    preview = data.get("text_preview", "")
    if preview:
        st.text_area("Text Preview", preview, height=120, disabled=True)


def _render_error(data: dict[str, Any]) -> None:
    msg = data.get("error_message", "")
    trace = data.get("stack_trace", "")
    if msg:
        st.error(msg)
    if trace:
        st.text_area("Stack Trace", trace, height=200, disabled=True)
