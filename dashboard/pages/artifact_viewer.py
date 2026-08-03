"""
dashboard/pages/artifact_viewer.py
=====================================
Artifact Viewer page.

Browse artifacts for any execution run:
- Screenshots displayed as images
- Trace zip info (download link)
- Video file info
- Lists of log files

Uses ArtifactService to resolve filesystem paths from the run_id.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from dashboard.components.report_table import render_run_selector
from dashboard.services.artifact_service import ArtifactService
from dashboard.services.report_loader import ReportLoader


def render(report_dir: Path | None = None, artifacts_root: Path | None = None) -> None:
    """Render the Artifact Viewer page."""
    st.title("📁 Artifact Viewer")

    loader = ReportLoader(report_dir)
    rows = loader.get_summary_rows()
    service = ArtifactService(artifacts_root)

    run_id = render_run_selector(rows, key="artifact_viewer_run")
    if not run_id:
        return

    st.markdown(f"**Run ID:** `{run_id}`")

    if not service.artifact_exists(run_id):
        st.warning(f"No artifact directory found for run: `{run_id}`")
        # Fall back to showing artifact paths from the report JSON
        report = loader.load_report(run_id)
        if report:
            _render_from_report(report, service)
        return

    artifacts = service.list_artifacts_for_run(run_id)

    # ---------- Screenshots ----------
    screenshots = artifacts["screenshots"]
    with st.expander(f"📸 Screenshots ({len(screenshots)})", expanded=True):
        if not screenshots:
            st.info("No screenshots captured.")
        else:
            cols = st.columns(min(len(screenshots), 3))
            for i, path in enumerate(screenshots):
                with cols[i % 3]:
                    try:
                        st.image(str(path), caption=path.name, use_container_width=True)
                    except Exception:
                        st.markdown(f"• `{path.name}` — {_human_size(path)}")

    # ---------- Traces ----------
    traces = artifacts["traces"]
    with st.expander(f"🔬 Traces ({len(traces)})"):
        if not traces:
            st.info("No trace files captured.")
        else:
            for path in traces:
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"`{path.name}`")
                col2.markdown(f"_{_human_size(path)}_")
                with open(path, "rb") as f:
                    st.download_button(
                        label=f"Download {path.name}",
                        data=f,
                        file_name=path.name,
                        mime="application/zip",
                        key=f"trace_{path.name}_{run_id}",
                    )

    # ---------- Videos ----------
    videos = artifacts["videos"]
    with st.expander(f"🎬 Videos ({len(videos)})"):
        if not videos:
            st.info("No videos captured.")
        else:
            for path in videos:
                try:
                    st.video(str(path))
                    st.caption(f"{path.name}  {_human_size(path)}")
                except Exception:
                    st.markdown(f"• `{path.name}` — {_human_size(path)}")

    # ---------- Logs ----------
    logs = artifacts["logs"]
    with st.expander(f"📄 Logs ({len(logs)})"):
        if not logs:
            st.info("No log files captured.")
        else:
            for path in logs:
                st.markdown(f"• `{path.name}` — {_human_size(path)}")


def _render_from_report(report: dict[str, Any], service: ArtifactService) -> None:
    """Fallback: render artifact info from the JSON report when filesystem dir is missing."""
    st.info("Showing artifact metadata from report JSON (files may not exist locally).")
    for section in report.get("sections", []):
        if section.get("section_type") == "artifacts":
            parsed = service.extract_from_report_section(section.get("data", {}))
            for group, entries in parsed.items():
                if entries:
                    with st.expander(f"{group.capitalize()} ({len(entries)})"):
                        for entry in entries:
                            st.markdown(
                                f"• **{entry.get('name', '?')}**  "
                                f"`{entry.get('path', '?')}`  "
                                f"({entry.get('size_bytes', 0):,} bytes)"
                            )


def _human_size(path: Path) -> str:
    """Return a human-readable file size string."""
    try:
        size = path.stat().st_size
        if size >= 1_048_576:
            return f"{size / 1_048_576:.1f} MB"
        if size >= 1_024:
            return f"{size / 1_024:.1f} KB"
        return f"{size} B"
    except OSError:
        return "?"
