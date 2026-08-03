"""
Tests for reports/report_builder.py
"""
from __future__ import annotations

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from execution.enums import ExecutionStatus, ArtifactType
from execution.models.artifact import Artifact
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.execution_result import ExecutionResult
from reports.models.report import Report
from reports.models.report_section import (
    ArtifactsPayload,
    BrowserStatePayload,
    ConsoleLogsPayload,
    DOMPayload,
    ErrorPayload,
    NetworkPayload,
    SectionType,
    SummaryPayload,
)
from reports.report_builder import ReportBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(hour=10, minute=0, second=0) -> datetime:
    return datetime(2024, 6, 1, hour, minute, second)


def _passed_result(**kwargs) -> ExecutionResult:
    defaults = dict(
        run_id="test-run-001",
        status=ExecutionStatus.PASSED,
        started_at=_dt(10, 0, 0),
        completed_at=_dt(10, 1, 30),
    )
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


def _failed_result(**kwargs) -> ExecutionResult:
    defaults = dict(
        run_id="test-run-002",
        status=ExecutionStatus.FAILED,
        started_at=_dt(9, 0, 0),
        completed_at=_dt(9, 0, 45),
        error_message="Element not found",
        stack_trace="Traceback...\nAssertionError",
    )
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


# ---------------------------------------------------------------------------
# ReportBuilder.build — summary section
# ---------------------------------------------------------------------------

class TestReportBuilderSummary:
    def test_summary_section_always_present(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.SUMMARY) is not None

    def test_summary_status_passed(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        section = report.get_section(SectionType.SUMMARY)
        assert section.data.status == "PASSED"

    def test_summary_status_failed(self):
        builder = ReportBuilder()
        report = builder.build(_failed_result())
        section = report.get_section(SectionType.SUMMARY)
        assert section.data.status == "FAILED"

    def test_summary_run_id(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        section = report.get_section(SectionType.SUMMARY)
        assert section.data.run_id == "test-run-001"

    def test_summary_duration_seconds(self):
        builder = ReportBuilder()
        result = _passed_result()
        report = builder.build(result)
        section = report.get_section(SectionType.SUMMARY)
        # 10:01:30 - 10:00:00 = 90 seconds
        assert section.data.duration_seconds == pytest.approx(90.0)

    def test_summary_environment_and_browser(self):
        builder = ReportBuilder()
        report = builder.build(
            _passed_result(),
            environment="staging",
            browser_type="chromium",
        )
        s = report.get_section(SectionType.SUMMARY)
        assert s.data.environment == "staging"
        assert s.data.browser_type == "chromium"

    def test_summary_tags(self):
        builder = ReportBuilder()
        report = builder.build(
            _passed_result(),
            tags=["smoke", "regression"],
        )
        s = report.get_section(SectionType.SUMMARY)
        assert "smoke" in s.data.tags
        assert "regression" in s.data.tags

    def test_report_title_default(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.title == "Execution Report"

    def test_report_title_custom(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result(), title="My Custom Report")
        assert report.title == "My Custom Report"


# ---------------------------------------------------------------------------
# ReportBuilder.build — error section
# ---------------------------------------------------------------------------

class TestReportBuilderError:
    def test_no_error_section_when_passed(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.ERROR) is None

    def test_error_section_when_failed(self):
        builder = ReportBuilder()
        report = builder.build(_failed_result())
        assert report.get_section(SectionType.ERROR) is not None

    def test_error_message(self):
        builder = ReportBuilder()
        report = builder.build(_failed_result())
        section = report.get_section(SectionType.ERROR)
        assert "Element not found" in section.data.error_message

    def test_stack_trace_included(self):
        builder = ReportBuilder()
        report = builder.build(_failed_result())
        section = report.get_section(SectionType.ERROR)
        assert section.data.stack_trace is not None
        assert "AssertionError" in section.data.stack_trace

    def test_error_no_stack_trace(self):
        builder = ReportBuilder()
        result = ExecutionResult(
            run_id="r3",
            status=ExecutionStatus.ERROR,
            started_at=_dt(),
            completed_at=_dt(minute=1),
            error_message="Something went wrong",
        )
        report = builder.build(result)
        section = report.get_section(SectionType.ERROR)
        assert section.data.stack_trace is None


# ---------------------------------------------------------------------------
# ReportBuilder.build — artifacts section
# ---------------------------------------------------------------------------

class TestReportBuilderArtifacts:
    def test_artifacts_section_always_present(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.ARTIFACTS) is not None

    def test_artifacts_empty_bundle(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        section = report.get_section(SectionType.ARTIFACTS)
        assert section.data.total == 0

    def test_artifacts_screenshot_count(self):
        builder = ReportBuilder()
        screenshot = Artifact(
            name="shot.png",
            path=Path("artifacts/screenshots/shot.png"),
            artifact_type=ArtifactType.SCREENSHOT,
            size_bytes=2048,
        )
        bundle = ArtifactBundle(screenshots=[screenshot])
        result = ExecutionResult(
            run_id="r-art",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        section = report.get_section(SectionType.ARTIFACTS)
        assert len(section.data.screenshots) == 1
        assert section.data.screenshots[0].name == "shot.png"
        assert section.data.screenshots[0].size_bytes == 2048

    def test_artifacts_path_as_string(self):
        builder = ReportBuilder()
        artifact = Artifact(
            name="trace.zip",
            path=Path("artifacts/traces/trace.zip"),
            artifact_type=ArtifactType.TRACE,
            size_bytes=1024,
        )
        bundle = ArtifactBundle(traces=[artifact])
        result = ExecutionResult(
            run_id="r-trace",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        section = report.get_section(SectionType.ARTIFACTS)
        # path should be a string in the report model
        assert isinstance(section.data.traces[0].path, str)


# ---------------------------------------------------------------------------
# ReportBuilder.build — browser state section
# ---------------------------------------------------------------------------

class TestReportBuilderBrowserState:
    def _make_browser_state(self) -> MagicMock:
        state = MagicMock()
        state.current_url = "https://example.com/login"
        state.title = "Login Page"
        state.user_agent = "Mozilla/5.0"
        viewport = MagicMock()
        viewport.width = 1280
        viewport.height = 720
        state.viewport = viewport
        state.cookies = [{"name": "session", "value": "abc"}]
        state.local_storage = {"theme": "dark"}
        state.session_storage = {"cart": "[]", "user": "{}"}
        return state

    def test_browser_state_not_added_when_none(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.BROWSER_STATE) is None

    def test_browser_state_section_added(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        assert report.get_section(SectionType.BROWSER_STATE) is not None

    def test_browser_state_url(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        section = report.get_section(SectionType.BROWSER_STATE)
        assert section.data.current_url == "https://example.com/login"

    def test_browser_state_viewport(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        section = report.get_section(SectionType.BROWSER_STATE)
        assert section.data.viewport_width == 1280
        assert section.data.viewport_height == 720

    def test_browser_state_cookie_count(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        section = report.get_section(SectionType.BROWSER_STATE)
        assert section.data.cookie_count == 1

    def test_browser_state_local_storage_keys(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        section = report.get_section(SectionType.BROWSER_STATE)
        assert "theme" in section.data.local_storage_keys

    def test_browser_state_session_storage_keys(self):
        builder = ReportBuilder()
        state = self._make_browser_state()
        report = builder.build(_passed_result(), browser_state=state)
        section = report.get_section(SectionType.BROWSER_STATE)
        assert "cart" in section.data.session_storage_keys
        assert "user" in section.data.session_storage_keys


# ---------------------------------------------------------------------------
# ReportBuilder.build — console logs section
# ---------------------------------------------------------------------------

class TestReportBuilderConsoleLogs:
    def _make_log_entry(self, level="INFO", message="hello", timestamp=None):
        entry = MagicMock()
        entry.level = level
        entry.message = message
        entry.timestamp = timestamp
        return entry

    def test_no_console_logs_section_when_empty(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.CONSOLE_LOGS) is None

    def test_console_logs_section_present_when_non_empty(self):
        builder = ReportBuilder()
        bundle = ArtifactBundle(console_logs=[self._make_log_entry()])
        result = ExecutionResult(
            run_id="r-cl",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        assert report.get_section(SectionType.CONSOLE_LOGS) is not None

    def test_console_logs_levels_uppercased(self):
        builder = ReportBuilder()
        bundle = ArtifactBundle(
            console_logs=[
                self._make_log_entry(level="error", message="boom"),
                self._make_log_entry(level="warning", message="careful"),
            ]
        )
        result = ExecutionResult(
            run_id="r-cl2",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        section = report.get_section(SectionType.CONSOLE_LOGS)
        levels = [e.level for e in section.data.entries]
        assert "ERROR" in levels
        assert "WARNING" in levels

    def test_console_logs_count(self):
        builder = ReportBuilder()
        bundle = ArtifactBundle(
            console_logs=[self._make_log_entry() for _ in range(5)]
        )
        result = ExecutionResult(
            run_id="r-cl3",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        section = report.get_section(SectionType.CONSOLE_LOGS)
        assert len(section.data.entries) == 5


# ---------------------------------------------------------------------------
# ReportBuilder.build — network section
# ---------------------------------------------------------------------------

class TestReportBuilderNetwork:
    def _make_network_events(self, requests=None, responses=None, failures=None):
        events = MagicMock()
        events.requests = requests or []
        events.responses = responses or []
        events.failures = failures or []
        return events

    def test_no_network_section_when_none(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.NETWORK) is None

    def test_network_section_present_when_events(self):
        builder = ReportBuilder()
        req = MagicMock()
        req.method = "GET"
        req.url = "https://api.example.com/data"
        req.resource_type = "fetch"
        events = self._make_network_events(requests=[req])
        bundle = ArtifactBundle(network_events=events)
        result = ExecutionResult(
            run_id="r-net",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        assert report.get_section(SectionType.NETWORK) is not None

    def test_network_request_count(self):
        builder = ReportBuilder()
        req = MagicMock()
        req.method = "POST"
        req.url = "https://api.example.com/submit"
        req.resource_type = "xhr"
        events = self._make_network_events(requests=[req, req])
        bundle = ArtifactBundle(network_events=events)
        result = ExecutionResult(
            run_id="r-net2",
            status=ExecutionStatus.PASSED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
        )
        report = builder.build(result)
        section = report.get_section(SectionType.NETWORK)
        assert len(section.data.requests) == 2

    def test_network_failure(self):
        builder = ReportBuilder()
        fail = MagicMock()
        fail.url = "https://broken.example.com"
        fail.method = "GET"
        fail.failure_text = "net::ERR_CONNECTION_REFUSED"
        events = self._make_network_events(failures=[fail])
        bundle = ArtifactBundle(network_events=events)
        result = ExecutionResult(
            run_id="r-net3",
            status=ExecutionStatus.FAILED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
            error_message="Network failure",
        )
        report = builder.build(result)
        section = report.get_section(SectionType.NETWORK)
        assert section.data.has_failures is True
        assert "ERR_CONNECTION_REFUSED" in section.data.failures[0].failure_text


# ---------------------------------------------------------------------------
# ReportBuilder.build — DOM section
# ---------------------------------------------------------------------------

class TestReportBuilderDOM:
    def _make_dom(self) -> MagicMock:
        snap = MagicMock()
        snap.url = "https://example.com/page"
        snap.html = "<html><body>Hello World</body></html>"
        snap.text_content = "Hello World"
        return snap

    def test_no_dom_section_when_none(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.get_section(SectionType.DOM) is None

    def test_dom_section_present(self):
        builder = ReportBuilder()
        snap = self._make_dom()
        report = builder.build(_passed_result(), dom_snapshot=snap)
        assert report.get_section(SectionType.DOM) is not None

    def test_dom_url(self):
        builder = ReportBuilder()
        snap = self._make_dom()
        report = builder.build(_passed_result(), dom_snapshot=snap)
        section = report.get_section(SectionType.DOM)
        assert section.data.url == "https://example.com/page"

    def test_dom_html_size_bytes(self):
        builder = ReportBuilder()
        snap = self._make_dom()
        report = builder.build(_passed_result(), dom_snapshot=snap)
        section = report.get_section(SectionType.DOM)
        expected = len("<html><body>Hello World</body></html>".encode("utf-8"))
        assert section.data.html_size_bytes == expected

    def test_dom_text_preview_truncated_at_500(self):
        builder = ReportBuilder()
        snap = MagicMock()
        snap.url = "https://example.com"
        snap.html = "<html/>"
        snap.text_content = "A" * 1000  # 1000 chars
        report = builder.build(_passed_result(), dom_snapshot=snap)
        section = report.get_section(SectionType.DOM)
        assert len(section.data.text_preview) == 500


# ---------------------------------------------------------------------------
# ReportBuilder — report structure
# ---------------------------------------------------------------------------

class TestReportBuilderStructure:
    def test_report_run_id(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.run_id == "test-run-001"

    def test_report_status(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.status == "PASSED"

    def test_returned_type_is_report(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert isinstance(report, Report)

    def test_section_order_summary_first(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        assert report.sections[0].section_type == SectionType.SUMMARY

    def test_section_order_error_second_when_present(self):
        builder = ReportBuilder()
        report = builder.build(_failed_result())
        # Summary = 0, Error = 1
        assert report.sections[1].section_type == SectionType.ERROR

    def test_minimum_sections_count_passed(self):
        builder = ReportBuilder()
        report = builder.build(_passed_result())
        # At minimum: Summary + Artifacts
        assert len(report.sections) >= 2

    def test_full_enriched_report_section_count(self):
        builder = ReportBuilder()
        state = MagicMock()
        state.current_url = "https://example.com"
        state.title = ""
        state.user_agent = ""
        state.viewport = None
        state.cookies = []
        state.local_storage = {}
        state.session_storage = {}

        snap = MagicMock()
        snap.url = "https://example.com"
        snap.html = "<html/>"
        snap.text_content = ""

        log = MagicMock()
        log.level = "INFO"
        log.message = "page loaded"
        log.timestamp = None

        net_req = MagicMock()
        net_req.method = "GET"
        net_req.url = "https://example.com"
        net_req.resource_type = "document"
        net_events = MagicMock()
        net_events.requests = [net_req]
        net_events.responses = []
        net_events.failures = []

        bundle = ArtifactBundle(
            console_logs=[log],
            network_events=net_events,
        )
        result = ExecutionResult(
            run_id="r-full",
            status=ExecutionStatus.FAILED,
            artifacts=bundle,
            started_at=_dt(),
            completed_at=_dt(minute=1),
            error_message="fail",
        )
        report = builder.build(
            result,
            browser_state=state,
            dom_snapshot=snap,
        )
        section_types = [s.section_type for s in report.sections]
        assert SectionType.SUMMARY in section_types
        assert SectionType.ERROR in section_types
        assert SectionType.ARTIFACTS in section_types
        assert SectionType.BROWSER_STATE in section_types
        assert SectionType.CONSOLE_LOGS in section_types
        assert SectionType.NETWORK in section_types
        assert SectionType.DOM in section_types
