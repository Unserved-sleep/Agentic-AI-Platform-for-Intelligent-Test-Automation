"""
Tests for reports/models/report.py and reports/models/report_section.py
"""
from __future__ import annotations

import pytest
from datetime import datetime

from reports.models.report import Report
from reports.models.report_section import (
    ArtifactEntry,
    ArtifactsPayload,
    BrowserStatePayload,
    ConsoleLogEntry,
    ConsoleLogsPayload,
    DOMPayload,
    ErrorPayload,
    NetworkFailureEntry,
    NetworkPayload,
    NetworkRequestEntry,
    NetworkResponseEntry,
    ReportSection,
    SectionType,
    SummaryPayload,
)


# ---------------------------------------------------------------------------
# SummaryPayload
# ---------------------------------------------------------------------------

class TestSummaryPayload:
    def test_basic_construction(self):
        p = SummaryPayload(
            run_id="r1",
            status="PASSED",
            started_at=datetime(2024, 1, 1, 10, 0),
            completed_at=datetime(2024, 1, 1, 10, 1),
            duration_seconds=60.0,
        )
        assert p.run_id == "r1"
        assert p.status == "PASSED"
        assert p.duration_seconds == 60.0

    def test_defaults(self):
        p = SummaryPayload(
            run_id="r2",
            status="FAILED",
            started_at=datetime(2024, 1, 1),
            completed_at=datetime(2024, 1, 1),
            duration_seconds=0.0,
        )
        assert p.environment == ""
        assert p.browser_type == ""
        assert p.tags == []

    def test_with_optional_fields(self):
        p = SummaryPayload(
            run_id="r3",
            status="PASSED",
            started_at=datetime(2024, 1, 1),
            completed_at=datetime(2024, 1, 1),
            duration_seconds=1.5,
            environment="staging",
            browser_type="chromium",
            tags=["smoke", "auth"],
        )
        assert p.environment == "staging"
        assert "smoke" in p.tags

    def test_immutable(self):
        p = SummaryPayload(
            run_id="r4",
            status="PASSED",
            started_at=datetime(2024, 1, 1),
            completed_at=datetime(2024, 1, 1),
            duration_seconds=0.0,
        )
        with pytest.raises(Exception):
            p.status = "FAILED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ArtifactsPayload
# ---------------------------------------------------------------------------

class TestArtifactsPayload:
    def test_empty_total(self):
        p = ArtifactsPayload()
        assert p.total == 0

    def test_total_counts_all_groups(self):
        e = ArtifactEntry(name="x", artifact_type="screenshot", path="/x", size_bytes=1)
        p = ArtifactsPayload(
            screenshots=[e],
            traces=[e],
            videos=[e],
            logs=[e],
        )
        assert p.total == 4

    def test_partial_groups(self):
        e = ArtifactEntry(name="s", artifact_type="screenshot", path="/s", size_bytes=100)
        p = ArtifactsPayload(screenshots=[e, e])
        assert p.total == 2


# ---------------------------------------------------------------------------
# ConsoleLogsPayload
# ---------------------------------------------------------------------------

class TestConsoleLogsPayload:
    def test_error_count(self):
        entries = [
            ConsoleLogEntry(level="ERROR", message="err1"),
            ConsoleLogEntry(level="ERROR", message="err2"),
            ConsoleLogEntry(level="INFO", message="ok"),
        ]
        p = ConsoleLogsPayload(entries=entries)
        assert p.error_count == 2
        assert p.warning_count == 0

    def test_warning_count(self):
        entries = [
            ConsoleLogEntry(level="WARNING", message="w"),
            ConsoleLogEntry(level="INFO", message="i"),
        ]
        p = ConsoleLogsPayload(entries=entries)
        assert p.warning_count == 1
        assert p.error_count == 0

    def test_empty(self):
        p = ConsoleLogsPayload()
        assert p.error_count == 0
        assert p.warning_count == 0


# ---------------------------------------------------------------------------
# NetworkPayload
# ---------------------------------------------------------------------------

class TestNetworkPayload:
    def test_has_failures_true(self):
        f = NetworkFailureEntry(url="http://x.com", method="GET", failure_text="ECONNRESET")
        p = NetworkPayload(failures=[f])
        assert p.has_failures is True

    def test_has_failures_false(self):
        p = NetworkPayload()
        assert p.has_failures is False


# ---------------------------------------------------------------------------
# Report model
# ---------------------------------------------------------------------------

class TestReport:
    def _make_section(self, stype: SectionType) -> ReportSection:
        return ReportSection(
            title=stype.value.replace("_", " ").title(),
            section_type=stype,
            data=None,
        )

    def test_passed_property(self):
        r = Report(
            run_id="r1",
            status="PASSED",
            sections=[],
        )
        assert r.passed is True
        assert r.failed is False

    def test_failed_property(self):
        r = Report(
            run_id="r1",
            status="FAILED",
            sections=[],
        )
        assert r.failed is True
        assert r.passed is False

    def test_get_section_found(self):
        s = self._make_section(SectionType.SUMMARY)
        r = Report(run_id="r1", status="PASSED", sections=[s])
        found = r.get_section(SectionType.SUMMARY)
        assert found is s

    def test_get_section_not_found(self):
        r = Report(run_id="r1", status="PASSED", sections=[])
        assert r.get_section(SectionType.ERROR) is None

    def test_get_all_sections(self):
        s1 = self._make_section(SectionType.ARTIFACTS)
        s2 = self._make_section(SectionType.ARTIFACTS)
        s3 = self._make_section(SectionType.SUMMARY)
        r = Report(run_id="r1", status="PASSED", sections=[s1, s2, s3])
        all_artifacts = r.get_all_sections(SectionType.ARTIFACTS)
        assert len(all_artifacts) == 2

    def test_immutable(self):
        r = Report(run_id="r1", status="PASSED", sections=[])
        with pytest.raises(Exception):
            r.status = "FAILED"  # type: ignore[misc]

    def test_generated_at_default(self):
        r = Report(run_id="r1", status="PASSED", sections=[])
        assert isinstance(r.generated_at, datetime)

    def test_metadata_default_empty(self):
        r = Report(run_id="r1", status="PASSED", sections=[])
        assert r.metadata == {}
