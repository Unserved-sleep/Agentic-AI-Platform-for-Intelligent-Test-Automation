"""
tests/dashboard/test_report_loader.py
=======================================
Unit tests for dashboard.services.report_loader.ReportLoader.

All tests use a tmp_path fixture so they never touch real report files.
No Streamlit import — pure Python.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dashboard.services.report_loader import ReportLoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(
    run_id: str = "run-001",
    status: str = "PASSED",
    duration: float = 2.5,
    environment: str = "staging",
    browser_type: str = "chromium",
    generated_at: str | None = None,
) -> dict:
    ts = generated_at or datetime.now(timezone.utc).isoformat()
    return {
        "run_id": run_id,
        "status": status,
        "title": f"Report for {run_id}",
        "generated_at": ts,
        "metadata": {},
        "sections": [
            {
                "title": "Summary",
                "section_type": "summary",
                "data": {
                    "run_id": run_id,
                    "status": status,
                    "started_at": ts,
                    "completed_at": ts,
                    "duration_seconds": duration,
                    "environment": environment,
                    "browser_type": browser_type,
                    "tags": [],
                },
            }
        ],
    }


def _write_report(directory: Path, report: dict) -> Path:
    path = directory / f"{report['run_id']}.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# ReportLoader.list_reports
# ---------------------------------------------------------------------------


class TestListReports:
    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        loader = ReportLoader(tmp_path)
        assert loader.list_reports() == []

    def test_missing_dir_returns_empty_list(self, tmp_path: Path) -> None:
        loader = ReportLoader(tmp_path / "nonexistent")
        assert loader.list_reports() == []

    def test_single_report_returned(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-abc"))
        loader = ReportLoader(tmp_path)
        reports = loader.list_reports()
        assert len(reports) == 1
        assert reports[0]["run_id"] == "run-abc"

    def test_multiple_reports_sorted_newest_first(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001", generated_at="2024-01-01T10:00:00+00:00"))
        _write_report(tmp_path, _make_report("run-002", generated_at="2024-06-01T10:00:00+00:00"))
        _write_report(tmp_path, _make_report("run-003", generated_at="2024-03-01T10:00:00+00:00"))
        loader = ReportLoader(tmp_path)
        reports = loader.list_reports()
        assert len(reports) == 3
        assert reports[0]["run_id"] == "run-002"
        assert reports[2]["run_id"] == "run-001"

    def test_malformed_json_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("not json{{{", encoding="utf-8")
        _write_report(tmp_path, _make_report("run-ok"))
        loader = ReportLoader(tmp_path)
        reports = loader.list_reports()
        assert len(reports) == 1
        assert reports[0]["run_id"] == "run-ok"

    def test_non_dict_json_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "array.json").write_text("[1, 2, 3]", encoding="utf-8")
        loader = ReportLoader(tmp_path)
        assert loader.list_reports() == []

    def test_only_json_files_loaded(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001"))
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
        loader = ReportLoader(tmp_path)
        assert len(loader.list_reports()) == 1


# ---------------------------------------------------------------------------
# ReportLoader.load_report
# ---------------------------------------------------------------------------


class TestLoadReport:
    def test_load_existing_report(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-xyz"))
        loader = ReportLoader(tmp_path)
        report = loader.load_report("run-xyz")
        assert report is not None
        assert report["run_id"] == "run-xyz"

    def test_missing_run_id_returns_none(self, tmp_path: Path) -> None:
        loader = ReportLoader(tmp_path)
        assert loader.load_report("nonexistent") is None

    def test_report_has_expected_top_level_keys(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001"))
        report = ReportLoader(tmp_path).load_report("run-001")
        for key in ("run_id", "status", "title", "generated_at", "sections"):
            assert key in report


# ---------------------------------------------------------------------------
# ReportLoader.get_summary_rows
# ---------------------------------------------------------------------------


class TestGetSummaryRows:
    def test_empty_returns_empty(self, tmp_path: Path) -> None:
        assert ReportLoader(tmp_path).get_summary_rows() == []

    def test_row_contains_required_fields(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001", duration=3.7, environment="prod"))
        rows = ReportLoader(tmp_path).get_summary_rows()
        assert len(rows) == 1
        row = rows[0]
        assert row["run_id"] == "run-001"
        assert row["status"] == "PASSED"
        assert row["duration_seconds"] == 3.7
        assert row["environment"] == "prod"

    def test_rows_without_summary_section_default_gracefully(self, tmp_path: Path) -> None:
        report = {"run_id": "run-x", "status": "FAILED", "title": "x", "generated_at": "t", "sections": []}
        _write_report(tmp_path, report)
        rows = ReportLoader(tmp_path).get_summary_rows()
        assert len(rows) == 1
        assert rows[0]["run_id"] == "run-x"
        assert rows[0]["duration_seconds"] == 0.0


# ---------------------------------------------------------------------------
# ReportLoader.compute_stats
# ---------------------------------------------------------------------------


class TestComputeStats:
    def test_empty_dir(self, tmp_path: Path) -> None:
        stats = ReportLoader(tmp_path).compute_stats()
        assert stats["total"] == 0
        assert stats["pass_rate"] == 0.0

    def test_all_passed(self, tmp_path: Path) -> None:
        for i in range(3):
            _write_report(tmp_path, _make_report(f"run-{i:03d}", status="PASSED", duration=1.0))
        stats = ReportLoader(tmp_path).compute_stats()
        assert stats["total"] == 3
        assert stats["passed"] == 3
        assert stats["failed"] == 0
        assert stats["pass_rate"] == 100.0

    def test_mixed_statuses(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001", status="PASSED", duration=2.0))
        _write_report(tmp_path, _make_report("run-002", status="FAILED", duration=4.0))
        _write_report(tmp_path, _make_report("run-003", status="PASSED", duration=2.0))
        stats = ReportLoader(tmp_path).compute_stats()
        assert stats["total"] == 3
        assert stats["passed"] == 2
        assert stats["failed"] == 1
        assert stats["pass_rate"] == pytest.approx(66.7, abs=0.1)

    def test_avg_duration(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001", duration=2.0))
        _write_report(tmp_path, _make_report("run-002", duration=4.0))
        stats = ReportLoader(tmp_path).compute_stats()
        assert stats["avg_duration_seconds"] == pytest.approx(3.0)

    def test_error_counted_correctly(self, tmp_path: Path) -> None:
        _write_report(tmp_path, _make_report("run-001", status="PASSED"))
        _write_report(tmp_path, _make_report("run-002", status="ERROR"))
        stats = ReportLoader(tmp_path).compute_stats()
        assert stats["error"] == 1
        assert stats["total"] == 2
