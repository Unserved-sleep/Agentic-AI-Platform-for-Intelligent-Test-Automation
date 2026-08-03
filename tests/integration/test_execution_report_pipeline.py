"""
tests/integration/test_execution_report_pipeline.py
======================================================
Integration test: ExecutionService → ReportAgent pipeline.

Verifies that after a successful execution:
  - artifacts/reports/<run_id>.json  is created
  - artifacts/reports/<run_id>.html  is created
  - artifacts/reports/<run_id>.md    is created

And that a failed execution also produces reports (report generation
must not be affected by test status).

These tests use a real Playwright browser (chromium, headless) and
write to a temporary report directory so they never pollute
artifacts/reports/ during CI.

Marks: integration — run with  pytest -m integration  or
                                pytest tests/integration/
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from execution.enums import ExecutionStatus, ExecutionType
from execution.models.execution_request import ExecutionRequest
from execution.services.execution_service import ExecutionService
from reports.report_agent import ReportAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(run_id: str | None = None) -> ExecutionRequest:
    return ExecutionRequest(
        run_id=run_id or str(uuid4()),
        execution_type=ExecutionType.UI,
        script_path="tests/dummy.py",
    )


def _passing_test(page):
    """Minimal Playwright test that always passes."""
    page.set_content("<h1>Integration Test</h1>")
    assert page.title() is not None  # trivially true


def _failing_test(page):
    """Minimal Playwright test that always fails."""
    page.set_content("<h1>Integration Test</h1>")
    raise AssertionError("Intentional test failure for report pipeline test")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExecutionReportPipeline:
    """End-to-end: ExecutionService + ReportAgent produce all three files."""

    def test_passed_execution_creates_all_three_reports(self, tmp_path: Path) -> None:
        """
        A passing execution must produce .json, .html, and .md report files.
        """
        service = ExecutionService()
        agent = ReportAgent(output_dir=tmp_path)
        request = _make_request()

        result = service.execute(request=request, test_function=_passing_test)

        assert result.status == ExecutionStatus.PASSED, (
            f"Expected PASSED, got {result.status.value}: {result.error_message}"
        )

        output = agent.generate(
            result,
            formats=["html", "json", "markdown"],
            title="Integration Test — Passed",
        )

        # All three paths must be returned
        assert output.json_path is not None
        assert output.html_path is not None
        assert output.markdown_path is not None

        # All three files must exist on disk
        assert output.json_path.exists(), f"JSON report not found: {output.json_path}"
        assert output.html_path.exists(), f"HTML report not found: {output.html_path}"
        assert output.markdown_path.exists(), f"Markdown report not found: {output.markdown_path}"

        # Files must be non-empty
        assert output.json_path.stat().st_size > 0
        assert output.html_path.stat().st_size > 0
        assert output.markdown_path.stat().st_size > 0

    def test_report_filenames_use_run_id(self, tmp_path: Path) -> None:
        """Report filenames must match the execution run_id."""
        service = ExecutionService()
        agent = ReportAgent(output_dir=tmp_path)
        request = _make_request()

        result = service.execute(request=request, test_function=_passing_test)
        output = agent.generate(result, formats=["html", "json", "markdown"])

        run_id = result.run_id
        assert output.json_path.name == f"{run_id}.json"
        assert output.html_path.name == f"{run_id}.html"
        assert output.markdown_path.name == f"{run_id}.md"

    def test_json_report_contains_run_id_and_status(self, tmp_path: Path) -> None:
        """The JSON report must contain run_id and status at the top level."""
        service = ExecutionService()
        agent = ReportAgent(output_dir=tmp_path)
        request = _make_request()

        result = service.execute(request=request, test_function=_passing_test)
        output = agent.generate(result, formats=["json"])

        data = json.loads(output.json_path.read_text(encoding="utf-8"))
        assert data["run_id"] == result.run_id
        assert data["status"] == "PASSED"

    def test_failed_execution_still_creates_reports(self, tmp_path: Path) -> None:
        """
        A failing test execution must also produce all three report files.
        Reports must be generated regardless of test status.
        """
        service = ExecutionService()
        agent = ReportAgent(output_dir=tmp_path)
        request = _make_request()

        result = service.execute(request=request, test_function=_failing_test)

        # Execution must register as failed/error — not passed
        assert result.status != ExecutionStatus.PASSED

        output = agent.generate(
            result,
            formats=["html", "json", "markdown"],
            title="Integration Test — Failed",
        )

        assert output.json_path.exists()
        assert output.html_path.exists()
        assert output.markdown_path.exists()

        # JSON must reflect the failed status
        data = json.loads(output.json_path.read_text(encoding="utf-8"))
        assert data["status"] != "PASSED"

    def test_report_generation_failure_does_not_affect_execution_result(
        self, tmp_path: Path
    ) -> None:
        """
        If the output_dir is read-only, ReportAgent.generate() raises, but
        ExecutionService.execute() already returned — the result is intact.
        """
        service = ExecutionService()
        request = _make_request()

        result = service.execute(request=request, test_function=_passing_test)

        # Make the output dir unwriteable to force a report error
        bad_dir = tmp_path / "readonly"
        bad_dir.mkdir()
        bad_dir.chmod(0o444)  # read-only

        agent = ReportAgent(output_dir=bad_dir)
        try:
            agent.generate(result, formats=["json"])
        except Exception:
            pass  # Expected — report generation fails

        # But the execution result is still valid and unchanged
        assert result.run_id is not None
        assert result.status == ExecutionStatus.PASSED

    def test_dashboard_loader_reads_generated_report(self, tmp_path: Path) -> None:
        """
        The JSON report written by ReportAgent must be parseable by
        dashboard.services.report_loader.ReportLoader — the end-to-end
        contract between the execution pipeline and the dashboard.
        """
        from dashboard.services.report_loader import ReportLoader

        service = ExecutionService()
        agent = ReportAgent(output_dir=tmp_path)
        request = _make_request()

        result = service.execute(request=request, test_function=_passing_test)
        agent.generate(result, formats=["json"])

        loader = ReportLoader(report_dir=tmp_path)
        reports = loader.list_reports()

        assert len(reports) == 1
        assert reports[0]["run_id"] == result.run_id
        assert reports[0]["status"] == "PASSED"

        rows = loader.get_summary_rows()
        assert len(rows) == 1
        assert rows[0]["run_id"] == result.run_id
