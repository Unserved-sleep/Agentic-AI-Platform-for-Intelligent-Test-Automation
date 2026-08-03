"""
dashboard/app.py
=================
Streamlit multi-page entry point for the Agentic AI Test Automation Dashboard.

Launch with:
    streamlit run dashboard/app.py

Pages
-----
- 🏠 Home               — summary KPIs and recent runs
- 📋 Execution History  — full sortable/filterable report table
- 🔍 Report Viewer      — per-report detail view with all sections
- 📁 Artifact Viewer    — browse screenshots, traces, videos, logs
- 📊 Analytics          — charts: trends, durations, status breakdown
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Streamlit path shim
# When Streamlit executes `streamlit run dashboard/app.py` it adds the
# *script's directory* (dashboard/) to sys.path — not the project root.
# We need the project root on sys.path so that the dashboard package itself
# and any sibling packages are importable.  This shim inserts the project
# root (parent of this file's directory) before any other imports.
# ---------------------------------------------------------------------------
_PROJ_ROOT = Path(__file__).parent.parent.resolve()
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))

import streamlit as st

# Import page render functions (relative imports — work both under Streamlit
# and under pytest/python -m)
from dashboard.pages.analytics import render as render_analytics
from dashboard.pages.artifact_viewer import render as render_artifacts
from dashboard.pages.execution_history import render as render_history
from dashboard.pages.home import render as render_home
from dashboard.pages.report_viewer import render as render_viewer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPORT_DIR = Path("artifacts") / "reports"
_ARTIFACTS_ROOT = Path("artifacts")

_PAGES: dict[str, tuple[str, object]] = {
    "Home": ("🏠 Home", render_home),
    "Execution History": ("📋 Execution History", render_history),
    "Report Viewer": ("🔍 Report Viewer", render_viewer),
    "Artifact Viewer": ("📁 Artifact Viewer", render_artifacts),
    "Analytics": ("📊 Analytics", render_analytics),
}

# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="AI Test Automation Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    with st.sidebar:
        st.image(
            "https://img.icons8.com/fluency/96/test-tube.png",
            width=60,
        )
        st.title("Test Automation")
        st.caption("Agentic AI Platform")
        st.markdown("---")

        page_labels = [label for label, _ in _PAGES.values()]
        selected_label = st.radio(
            "Navigate",
            options=page_labels,
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption(f"Reports dir: `{_REPORT_DIR}`")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()

    # Dispatch to the selected page
    for key, (label, render_fn) in _PAGES.items():
        if selected_label == label:
            if key == "Artifact Viewer":
                render_fn(report_dir=_REPORT_DIR, artifacts_root=_ARTIFACTS_ROOT)  # type: ignore[call-arg]
            else:
                render_fn(report_dir=_REPORT_DIR)  # type: ignore[call-arg]
            break


if __name__ == "__main__":
    main()
