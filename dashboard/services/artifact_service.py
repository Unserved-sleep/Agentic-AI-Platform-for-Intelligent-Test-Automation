"""
dashboard/services/artifact_service.py
========================================
Resolves and queries artifact files on disk.

Artifacts live under artifacts/<run_id>/{screenshots,traces,videos,logs}/.
This service maps the paths stored in a report's artifacts section
to real filesystem paths and exposes helpers for the Artifact Viewer page.

No dependency on the execution package — works purely with the
string paths stored inside the JSON report.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Root artifacts directory
_ARTIFACTS_ROOT = Path("artifacts")

# Recognised artifact sub-types and their directory names
_ARTIFACT_DIRS = {
    "screenshot": "screenshots",
    "screenshots": "screenshots",
    "trace": "traces",
    "traces": "traces",
    "video": "videos",
    "videos": "videos",
    "log": "logs",
    "logs": "logs",
}


class ArtifactService:
    """
    Resolves artifact paths and lists available artifact files.

    Parameters
    ----------
    artifacts_root:
        Root directory that contains per-run artifact subdirectories.
        Defaults to ``artifacts/``.
    """

    def __init__(self, artifacts_root: Optional[Path] = None) -> None:
        self.artifacts_root = artifacts_root or _ARTIFACTS_ROOT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_run_dir(self, run_id: str) -> Path:
        """Return the artifact directory for a given run_id."""
        return self.artifacts_root / run_id

    def list_artifacts_for_run(self, run_id: str) -> dict[str, list[Path]]:
        """
        Walk the run directory and return all artifact paths grouped by type.

        Parameters
        ----------
        run_id:
            Execution run identifier.

        Returns
        -------
        dict[str, list[Path]]
            Keys: ``screenshots``, ``traces``, ``videos``, ``logs``.
        """
        run_dir = self.get_run_dir(run_id)
        result: dict[str, list[Path]] = {
            "screenshots": [],
            "traces": [],
            "videos": [],
            "logs": [],
        }

        if not run_dir.exists():
            return result

        for subdir, key in [
            ("screenshots", "screenshots"),
            ("traces", "traces"),
            ("videos", "videos"),
            ("logs", "logs"),
        ]:
            d = run_dir / subdir
            if d.exists():
                result[key] = sorted(d.iterdir())

        return result

    def resolve_path(self, raw_path: str) -> Optional[Path]:
        """
        Resolve a path string from a report entry to an absolute Path.

        Tries the path as-is first, then relative to the artifacts root.

        Parameters
        ----------
        raw_path:
            Path string from an ArtifactEntry in the JSON report.

        Returns
        -------
        Path | None
            Resolved path if the file exists, else None.
        """
        p = Path(raw_path)
        if p.exists():
            return p

        # Try relative to artifacts root
        relative = self.artifacts_root / p
        if relative.exists():
            return relative

        logger.debug("Artifact not found at path: %s", raw_path)
        return None

    def get_screenshots(self, run_id: str) -> list[Path]:
        """Return all screenshot paths for a run."""
        return self.list_artifacts_for_run(run_id)["screenshots"]

    def get_traces(self, run_id: str) -> list[Path]:
        """Return all trace zip paths for a run."""
        return self.list_artifacts_for_run(run_id)["traces"]

    def get_videos(self, run_id: str) -> list[Path]:
        """Return all video paths for a run."""
        return self.list_artifacts_for_run(run_id)["videos"]

    def artifact_exists(self, run_id: str) -> bool:
        """Return True if the run directory exists and is non-empty."""
        run_dir = self.get_run_dir(run_id)
        if not run_dir.exists():
            return False
        return any(run_dir.iterdir())

    def extract_from_report_section(
        self, section_data: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Parse the artifacts section data dict from a JSON report.

        Parameters
        ----------
        section_data:
            The ``data`` field of a section with type ``artifacts``.

        Returns
        -------
        dict with keys ``screenshots``, ``traces``, ``videos``, ``logs``,
        each being a list of ArtifactEntry dicts.
        """
        return {
            "screenshots": section_data.get("screenshots", []),
            "traces": section_data.get("traces", []),
            "videos": section_data.get("videos", []),
            "logs": section_data.get("logs", []),
        }
