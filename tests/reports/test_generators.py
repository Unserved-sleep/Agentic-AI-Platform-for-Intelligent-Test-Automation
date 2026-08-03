"""
Tests for reports/generators/
- JSONGenerator
- MarkdownGenerator
- HTMLGenerator
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from reports.generators.json_generator import JSONGenerator, _default_serializer
from reports.generators.markdown_generator import MarkdownGenerator
from reports.generators.html_generator import HTMLGenerator
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
# Shared fixtures
# ---------------------------------------------------------------------------

def _dt(hour=10) -> datetime:
    return datetime(2024, 1, 15, hour, 0, 0)


def _summary_section(status="PASSED") -> ReportSection:
    return ReportSection(
        title="Summary",
        section_type=SectionType.SUMMARY,
        data=SummaryPayload(
            run_id="run-001",
            status=status,
            started_at=_dt(10),
            completed_at=_dt(10),
            duration_seconds=90.0,
            environment="staging",
            browser_type="chromium",
            tags=["smoke"],
        ),
    )


def _error_section() -> ReportSection:
    return ReportSection(
        title="Error",
        section_type=SectionType.ERROR,
        data=ErrorPayload(
            error_message="Element not found: #submit",
            stack_trace="Traceback:\n  line 42\nAssertionError",
        ),
    )


def _artifacts_section() -> ReportSection:
    entry = ArtifactEntry(
        name="screenshot.png",
        artifact_type="screenshot",
        path="/artifacts/screenshot.png",
        size_bytes=4096,
    )
    return ReportSection(
        title="Artifacts",
        section_type=SectionType.ARTIFACTS,
        data=ArtifactsPayload(screenshots=[entry]),
    )


def _console_section() -> ReportSection:
    return ReportSection(
        title="Console Logs",
        section_type=SectionType.CONSOLE_LOGS,
        data=ConsoleLogsPayload(
            entries=[
                ConsoleLogEntry(level="ERROR", message="Uncaught TypeError"),
                ConsoleLogEntry(level="INFO", message="Page loaded"),
            ]
        ),
    )


def _network_section() -> ReportSection:
    return ReportSection(
        title="Network",
        section_type=SectionType.NETWORK,
        data=NetworkPayload(
            requests=[
                NetworkRequestEntry(method="GET", url="https://api.test/data", resource_type="fetch")
            ],
            responses=[
                NetworkResponseEntry(url="https://api.test/data", status_code=200, status_text="OK", ok=True)
            ],
            failures=[
                NetworkFailureEntry(url="https://broken.test", method="POST", failure_text="ECONNRESET")
            ],
        ),
    )


def _browser_state_section() -> ReportSection:
    return ReportSection(
        title="Browser State",
        section_type=SectionType.BROWSER_STATE,
        data=BrowserStatePayload(
            current_url="https://example.com/login",
            title="Login",
            user_agent="Mozilla/5.0",
            viewport_width=1280,
            viewport_height=720,
            cookie_count=2,
            local_storage_keys=["theme"],
            session_storage_keys=["cart"],
        ),
    )


def _dom_section() -> ReportSection:
    return ReportSection(
        title="DOM Snapshot",
        section_type=SectionType.DOM,
        data=DOMPayload(
            url="https://example.com",
            html_size_bytes=1024,
            text_preview="Hello world",
        ),
    )


def _full_passed_report() -> Report:
    return Report(
        run_id="run-001",
        status="PASSED",
        title="Full Test Report",
        generated_at=datetime(2024, 1, 15, 12, 0, 0),
        sections=[
            _summary_section("PASSED"),
            _artifacts_section(),
            _browser_state_section(),
            _console_section(),
            _network_section(),
            _dom_section(),
        ],
    )


def _full_failed_report() -> Report:
    return Report(
        run_id="run-002",
        status="FAILED",
        title="Failed Test Report",
        generated_at=datetime(2024, 1, 15, 12, 0, 0),
        sections=[
            _summary_section("FAILED"),
            _error_section(),
            _artifacts_section(),
        ],
    )


# ---------------------------------------------------------------------------
# JSONGenerator
# ---------------------------------------------------------------------------

class TestJSONGenerator:
    def test_generate_returns_path(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        report = _full_passed_report()
        result = gen.generate(report, output)
        assert result == output

    def test_file_created(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_valid_json_output(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_run_id_in_json(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["run_id"] == "run-001"

    def test_status_in_json(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["status"] == "PASSED"

    def test_sections_in_json(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data["sections"], list)
        assert len(data["sections"]) > 0

    def test_datetime_serialised_as_iso(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        # generated_at should be ISO string
        assert "2024" in data["generated_at"]

    def test_section_type_is_string(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "report.json"
        gen.generate(_full_passed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        for section in data["sections"]:
            assert isinstance(section["section_type"], str)

    def test_creates_parent_directories(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "nested" / "dir" / "report.json"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_failed_report_json(self, tmp_path):
        gen = JSONGenerator()
        output = tmp_path / "failed.json"
        gen.generate(_full_failed_report(), output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["status"] == "FAILED"
        types = [s["section_type"] for s in data["sections"]]
        assert "error" in types

    def test_default_serializer_datetime(self):
        dt = datetime(2024, 6, 1, 12, 0, 0)
        result = _default_serializer(dt)
        assert "2024" in result

    def test_default_serializer_enum(self):
        from execution.enums import ExecutionStatus
        result = _default_serializer(ExecutionStatus.PASSED)
        assert result == "PASSED"

    def test_default_serializer_path(self):
        from pathlib import Path
        p = Path("/some/path")
        result = _default_serializer(p)
        assert Path(result) == p

    def test_default_serializer_unknown_raises(self):
        with pytest.raises(TypeError):
            _default_serializer(object())


# ---------------------------------------------------------------------------
# MarkdownGenerator
# ---------------------------------------------------------------------------

class TestMarkdownGenerator:
    def test_generate_returns_path(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        result = gen.generate(_full_passed_report(), output)
        assert result == output

    def test_file_created(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_contains_run_id(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "run-001" in content

    def test_contains_status_passed(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "PASSED" in content

    def test_contains_title(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "Full Test Report" in content

    def test_contains_section_headings(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "## Summary" in content
        assert "## Artifacts" in content

    def test_error_section_contains_message(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_failed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "Element not found" in content

    def test_error_section_contains_stack_trace_details(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_failed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "<details>" in content
        assert "Stack Trace" in content

    def test_artifact_table_present(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "screenshot.png" in content

    def test_console_logs_table_present(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "Uncaught TypeError" in content

    def test_network_table_present(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "api.test" in content

    def test_browser_state_table_present(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "https://example.com/login" in content

    def test_dom_section_present(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "report.md"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "DOM Snapshot" in content

    def test_creates_parent_directories(self, tmp_path):
        gen = MarkdownGenerator()
        output = tmp_path / "subdir" / "report.md"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_empty_artifacts_message(self, tmp_path):
        gen = MarkdownGenerator()
        report = Report(
            run_id="r-empty",
            status="PASSED",
            sections=[
                ReportSection(
                    title="Artifacts",
                    section_type=SectionType.ARTIFACTS,
                    data=ArtifactsPayload(),
                )
            ],
        )
        output = tmp_path / "empty.md"
        gen.generate(report, output)
        content = output.read_text(encoding="utf-8")
        assert "No artifacts collected" in content

    def test_format_property(self):
        gen = MarkdownGenerator()
        assert gen.format == "markdown"

    def test_escape_pipe_characters(self):
        gen = MarkdownGenerator()
        result = gen._escape("text|with|pipes")
        assert "|" not in result.replace("\\|", "")


# ---------------------------------------------------------------------------
# HTMLGenerator
# ---------------------------------------------------------------------------

class TestHTMLGenerator:
    def test_generate_returns_path(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        result = gen.generate(_full_passed_report(), output)
        assert result == output

    def test_file_created(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_valid_html_structure(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content

    def test_contains_run_id(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "run-001" in content

    def test_contains_status_badge(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "PASSED" in content

    def test_contains_title_in_head(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "<title>Full Test Report</title>" in content

    def test_sections_rendered(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_passed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "<section>" in content

    def test_error_section_in_html(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "report.html"
        gen.generate(_full_failed_report(), output)
        content = output.read_text(encoding="utf-8")
        assert "Element not found" in content

    def test_creates_parent_directories(self, tmp_path):
        gen = HTMLGenerator()
        output = tmp_path / "deep" / "nested" / "report.html"
        gen.generate(_full_passed_report(), output)
        assert output.exists()

    def test_format_property(self):
        gen = HTMLGenerator()
        assert gen.format == "html"
