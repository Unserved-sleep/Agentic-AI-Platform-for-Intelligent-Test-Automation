"""
dashboard/components/report_table.py
======================================
Tabular report list component.

Renders a styled pandas DataFrame table from a list of summary rows
produced by ``ReportLoader.get_summary_rows()``.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.status_badge import status_badge_html


def render_report_table(rows: list[dict[str, Any]], key: str = "report_table") -> None:
    """
    Render a searchable, filterable table of execution reports.

    Parameters
    ----------
    rows:
        List of row dicts from ``ReportLoader.get_summary_rows()``.
    key:
        Streamlit widget key prefix for uniqueness.
    """
    if not rows:
        st.info("No reports found. Run some tests first to generate reports.")
        return

    df = pd.DataFrame(rows)

    # Normalise columns to expected set
    expected_cols = [
        "run_id", "status", "title", "generated_at",
        "duration_seconds", "environment", "browser_type",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_cols]

    # Format duration
    df["duration_seconds"] = df["duration_seconds"].apply(
        lambda x: f"{float(x):.2f}s" if x not in ("", None) else "—"
    )

    # Rename for display
    df.columns = pd.Index([
        "Run ID", "Status", "Title", "Generated At",
        "Duration", "Environment", "Browser",
    ])

    # Status filter
    statuses = sorted(set(df["Status"].dropna().unique()))
    chosen = st.multiselect(
        "Filter by status",
        options=statuses,
        default=statuses,
        key=f"{key}_status_filter",
    )
    if chosen:
        df = df[df["Status"].isin(chosen)]

    # Search box
    search = st.text_input("Search by Run ID or Title", key=f"{key}_search")
    if search:
        mask = (
            df["Run ID"].str.contains(search, case=False, na=False)
            | df["Title"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.warning("No rows match the current filter.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"{len(df)} report(s) displayed")


def render_run_selector(
    rows: list[dict[str, Any]], key: str = "run_selector"
) -> str | None:
    """
    Render a selectbox for choosing a run_id.

    Parameters
    ----------
    rows:
        List of summary row dicts.
    key:
        Streamlit widget key.

    Returns
    -------
    str | None
        Selected run_id, or None if no reports.
    """
    if not rows:
        st.info("No reports available.")
        return None

    options = [r["run_id"] for r in rows]
    labels = [
        f"{r['run_id'][:8]}…  [{r.get('status', '?')}]  {r.get('generated_at', '')[:19]}"
        for r in rows
    ]
    label_to_id = dict(zip(labels, options))

    selected_label = st.selectbox(
        "Select a run",
        options=labels,
        key=key,
    )
    return label_to_id.get(selected_label) if selected_label else None
