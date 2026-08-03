"""
Tests for reports/report_agent.py — ReportAgent and ReportOutput
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from execution.enums import ExecutionStatus, ArtifactType
from execution.models.artifact import Artifact
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.execution_result import ExecutionResult
from reports.report_agent import ReportAgent, ReportOutput
from reports.models.report import Report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(hour=10, minute=0, second=0) -> datetime:
    return datetime(2024, 6, 1, hour, minute, second)


def _result(
    run_id="agent-run-001",
    status=ExecutionStatus.PASSED,
    error_message=None,
    stack_trace=None,
) -> ExecutionResult:
    return ExecutionResult(
        run_id=run_id,
        status=status,
        started_at=_dt(10),
        completed_at=_dt(10, 1),
        error_message=error_message,
        stack_trace=stack_trace,
    )


# ---------------------------------------------------------------------------
# ReportOutput dataclass
# ---------------------------------------------------------------------------

class TestReportOutput:
    def test_html_path_property(self, tmp_path):
        report = MagicMock(spec=Report)
        output = ReportOutput(report=report, paths={"html": tmp_path / "r.html"})
        assert output.html_path == tmp_path / "r.html"

    def test_json_path_property(self, tmp_path):
        report = MagicMock(spec=Report)
        output = ReportOutput(report=report, paths={"json": tmp_path / "r.json"})
        assert output.json_path == tmp_path / "r.json"

    def test_markdown_path_property(self, tmp_path):
        report = MagicMock(spec=Report)
        output = ReportOutput(report=report, paths={"markdown": tmp_path / "r.md"})
        assert output.markdown_path == tmp_path / "r.md"

    def test_missing_path_returns_none(self):
        report = MagicMock(spec=Report)
        output = ReportOutput(report=report, paths={})
        assert output.html_path is None
        assert output.json_path is None
        assert output.markdown_path is None

    def test_contains_report(self):
        report = MagicMock(spec=Report)
        output = ReportOutput(report=report)
        assert output.report is report


# ---------------------------------------------------------------------------
# ReportAgent.generate — basic
# ---------------------------------------------------------------------------

class TestReportAgentGenerate:
    def test_returns_report_output(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result()
        output = agent.generate(result, formats=["json"])
        assert isinstance(output, ReportOutput)

    def test_generates_all_three_formats(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result()
        output = agent.generate(result, formats=["html", "json", "markdown"])
        assert output.html_path is not None
        assert output.json_path is not None
        assert output.markdown_path is not None

    def test_default_formats_all_three(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result()
        output = agent.generate(result)
        assert output.html_path is not None
        assert output.json_path is not None
        assert output.markdown_path is not None

    def test_files_are_created_on_disk(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result()
        output = agent.generate(result, formats=["html", "json", "markdown"])
        assert output.html_path.exists()
        assert output.json_path.exists()
        assert output.markdown_path.exists()

    def test_html_extension_in_path(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["html"])
        assert output.html_path.suffix == ".html"

    def test_json_extension_in_path(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["json"])
        assert output.json_path.suffix == ".json"

    def test_markdown_extension_in_path(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["markdown"])
        assert output.markdown_path.suffix == ".md"

    def test_run_id_in_filename(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result(run_id="my-unique-run-xyz")
        output = agent.generate(result, formats=["json"])
        assert "my-unique-run-xyz" in output.json_path.name

    def test_report_model_attached(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["json"])
        assert isinstance(output.report, Report)

    def test_report_run_id_matches(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result(run_id="check-run-id")
        output = agent.generate(result, formats=["json"])
        assert output.report.run_id == "check-run-id"

    def test_report_status_passed(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(status=ExecutionStatus.PASSED), formats=["json"])
        assert output.report.status == "PASSED"

    def test_report_status_failed(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        result = _result(status=ExecutionStatus.FAILED, error_message="boom")
        output = agent.generate(result, formats=["json"])
        assert output.report.status == "FAILED"

    def test_invalid_format_raises_value_error(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        with pytest.raises(ValueError, match="Unsupported"):
            agent.generate(_result(), formats=["pdf"])

    def test_multiple_unsupported_formats_raises(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        with pytest.raises(ValueError, match="Unsupported"):
            agent.generate(_result(), formats=["pdf", "xml"])

    def test_custom_title_in_report(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(
            _result(), formats=["json"], title="Custom Title"
        )
        assert output.report.title == "Custom Title"

    def test_custom_output_dir_used(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path / "default")
        custom_dir = tmp_path / "custom"
        output = agent.generate(
            _result(), formats=["json"], output_dir=custom_dir
        )
        assert "custom" in str(output.json_path)

    def test_json_output_valid(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["json"])
        data = json.loads(output.json_path.read_text(encoding="utf-8"))
        assert "run_id" in data
        assert "sections" in data

    def test_environment_in_summary(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(
            _result(), formats=["json"], environment="production"
        )
        data = json.loads(output.json_path.read_text())
        summary_section = next(
            s for s in data["sections"] if s["section_type"] == "summary"
        )
        assert summary_section["data"]["environment"] == "production"

    def test_browser_type_in_summary(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(
            _result(), formats=["json"], browser_type="firefox"
        )
        data = json.loads(output.json_path.read_text())
        summary_section = next(
            s for s in data["sections"] if s["section_type"] == "summary"
        )
        assert summary_section["data"]["browser_type"] == "firefox"

    def test_tags_in_summary(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(
            _result(), formats=["json"], tags=["smoke", "auth"]
        )
        data = json.loads(output.json_path.read_text())
        summary_section = next(
            s for s in data["sections"] if s["section_type"] == "summary"
        )
        assert "smoke" in summary_section["data"]["tags"]


# ---------------------------------------------------------------------------
# ReportAgent — single-format convenience methods
# ---------------------------------------------------------------------------

class TestReportAgentConvenience:
    def test_generate_html_creates_file(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_html(_result(), output_path=tmp_path / "r.html")
        assert path.exists()
        assert path.suffix == ".html"

    def test_generate_json_creates_file(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_json(_result(), output_path=tmp_path / "r.json")
        assert path.exists()
        assert path.suffix == ".json"

    def test_generate_markdown_creates_file(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_markdown(_result(), output_path=tmp_path / "r.md")
        assert path.exists()
        assert path.suffix == ".md"

    def test_generate_html_default_path_uses_run_id(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_html(_result(run_id="my-run"))
        assert "my-run" in path.name
        assert path.suffix == ".html"

    def test_generate_json_default_path_uses_run_id(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_json(_result(run_id="my-json-run"))
        assert "my-json-run" in path.name
        assert path.suffix == ".json"

    def test_generate_markdown_default_path_uses_run_id(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_markdown(_result(run_id="my-md-run"))
        assert "my-md-run" in path.name
        assert path.suffix == ".md"

    def test_generate_json_returns_valid_json(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_json(_result(), output_path=tmp_path / "r.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["run_id"] == "agent-run-001"

    def test_generate_markdown_contains_run_id(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_markdown(_result(run_id="my-md-001"), output_path=tmp_path / "r.md")
        content = path.read_text(encoding="utf-8")
        assert "my-md-001" in content

    def test_generate_html_contains_run_id(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        path = agent.generate_html(_result(run_id="my-html-001"), output_path=tmp_path / "r.html")
        content = path.read_text(encoding="utf-8")
        assert "my-html-001" in content


# ---------------------------------------------------------------------------
# ReportAgent — enrichment options
# ---------------------------------------------------------------------------

class TestReportAgentEnrichment:
    def test_browser_state_included_when_provided(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        state = MagicMock()
        state.current_url = "https://example.com"
        state.title = "Home"
        state.user_agent = "Mozilla"
        state.viewport = None
        state.cookies = []
        state.local_storage = {}
        state.session_storage = {}
        output = agent.generate(
            _result(), formats=["json"], browser_state=state
        )
        data = json.loads(output.json_path.read_text())
        section_types = [s["section_type"] for s in data["sections"]]
        assert "browser_state" in section_types

    def test_dom_snapshot_included_when_provided(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        snap = MagicMock()
        snap.url = "https://example.com"
        snap.html = "<html/>"
        snap.text_content = "Hello"
        output = agent.generate(
            _result(), formats=["json"], dom_snapshot=snap
        )
        data = json.loads(output.json_path.read_text())
        section_types = [s["section_type"] for s in data["sections"]]
        assert "dom" in section_types

    def test_no_browser_state_section_when_not_provided(self, tmp_path):
        agent = ReportAgent(output_dir=tmp_path)
        output = agent.generate(_result(), formats=["json"])
        data = json.loads(output.json_path.read_text())
        section_types = [s["section_type"] for s in data["sections"]]
        assert "browser_state" not in section_types


# ---------------------------------------------------------------------------
# ReportAgent — extension helper
# ---------------------------------------------------------------------------

class TestReportAgentExtension:
    def test_html_extension(self):
        assert ReportAgent._extension("html") == "html"

    def test_json_extension(self):
        assert ReportAgent._extension("json") == "json"

    def test_markdown_extension(self):
        assert ReportAgent._extension("markdown") == "md"

    def test_unknown_format_returns_itself(self):
        assert ReportAgent._extension("pdf") == "pdf"
