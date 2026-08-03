"""
tests/dashboard/test_artifact_service.py
==========================================
Unit tests for dashboard.services.artifact_service.ArtifactService.

Uses tmp_path to build realistic artifact directory trees.
No Streamlit import — pure Python.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dashboard.services.artifact_service import ArtifactService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_dir(root: Path, run_id: str, types: list[str] | None = None) -> Path:
    """Create a realistic artifact dir structure for a run."""
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    for t in (types or []):
        sub = run_dir / t
        sub.mkdir()
        (sub / f"{t.rstrip('s')}.dummy").touch()
    return run_dir


# ---------------------------------------------------------------------------
# ArtifactService.get_run_dir
# ---------------------------------------------------------------------------


class TestGetRunDir:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        assert svc.get_run_dir("abc-123") == tmp_path / "abc-123"


# ---------------------------------------------------------------------------
# ArtifactService.artifact_exists
# ---------------------------------------------------------------------------


class TestArtifactExists:
    def test_returns_false_for_missing_run(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        assert svc.artifact_exists("missing-run") is False

    def test_returns_false_for_empty_dir(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-001"
        run_dir.mkdir()
        svc = ArtifactService(tmp_path)
        assert svc.artifact_exists("run-001") is False

    def test_returns_true_for_non_empty_dir(self, tmp_path: Path) -> None:
        _make_run_dir(tmp_path, "run-001", ["screenshots"])
        svc = ArtifactService(tmp_path)
        assert svc.artifact_exists("run-001") is True


# ---------------------------------------------------------------------------
# ArtifactService.list_artifacts_for_run
# ---------------------------------------------------------------------------


class TestListArtifactsForRun:
    def test_empty_result_for_missing_run(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        result = svc.list_artifacts_for_run("no-such-run")
        assert result == {"screenshots": [], "traces": [], "videos": [], "logs": []}

    def test_screenshots_found(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-001"
        ss_dir = run_dir / "screenshots"
        ss_dir.mkdir(parents=True)
        (ss_dir / "screenshot.png").write_bytes(b"\x89PNG")
        svc = ArtifactService(tmp_path)
        result = svc.list_artifacts_for_run("run-001")
        assert len(result["screenshots"]) == 1
        assert result["screenshots"][0].name == "screenshot.png"

    def test_multiple_types(self, tmp_path: Path) -> None:
        _make_run_dir(tmp_path, "run-002", ["screenshots", "traces", "videos"])
        svc = ArtifactService(tmp_path)
        result = svc.list_artifacts_for_run("run-002")
        assert len(result["screenshots"]) == 1
        assert len(result["traces"]) == 1
        assert len(result["videos"]) == 1
        assert result["logs"] == []

    def test_logs_found(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-003"
        log_dir = run_dir / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "execution.log").write_text("log data", encoding="utf-8")
        svc = ArtifactService(tmp_path)
        result = svc.list_artifacts_for_run("run-003")
        assert len(result["logs"]) == 1


# ---------------------------------------------------------------------------
# ArtifactService.resolve_path
# ---------------------------------------------------------------------------


class TestResolvePath:
    def test_resolves_existing_absolute_path(self, tmp_path: Path) -> None:
        target = tmp_path / "run-001" / "screenshots" / "shot.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"")
        svc = ArtifactService(tmp_path)
        assert svc.resolve_path(str(target)) == target

    def test_returns_none_for_nonexistent(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        assert svc.resolve_path("this/does/not/exist.png") is None


# ---------------------------------------------------------------------------
# ArtifactService.get_screenshots / get_traces / get_videos
# ---------------------------------------------------------------------------


class TestConvenienceAccessors:
    def test_get_screenshots(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-s"
        ss = run_dir / "screenshots"
        ss.mkdir(parents=True)
        (ss / "a.png").write_bytes(b"")
        (ss / "b.png").write_bytes(b"")
        svc = ArtifactService(tmp_path)
        assert len(svc.get_screenshots("run-s")) == 2

    def test_get_traces_empty(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        assert svc.get_traces("nonexistent") == []

    def test_get_videos_empty(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        assert svc.get_videos("nonexistent") == []


# ---------------------------------------------------------------------------
# ArtifactService.extract_from_report_section
# ---------------------------------------------------------------------------


class TestExtractFromReportSection:
    def test_parses_all_groups(self, tmp_path: Path) -> None:
        section_data = {
            "screenshots": [{"name": "s.png", "artifact_type": "screenshot", "path": "/p", "size_bytes": 100}],
            "traces": [],
            "videos": [],
            "logs": [{"name": "l.log", "artifact_type": "log", "path": "/l", "size_bytes": 50}],
        }
        svc = ArtifactService(tmp_path)
        result = svc.extract_from_report_section(section_data)
        assert len(result["screenshots"]) == 1
        assert result["screenshots"][0]["name"] == "s.png"
        assert result["traces"] == []
        assert len(result["logs"]) == 1

    def test_empty_section_data(self, tmp_path: Path) -> None:
        svc = ArtifactService(tmp_path)
        result = svc.extract_from_report_section({})
        assert result == {"screenshots": [], "traces": [], "videos": [], "logs": []}
