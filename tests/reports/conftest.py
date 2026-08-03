"""
Shared fixtures for reports tests.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path

from execution.enums import ExecutionStatus, ArtifactType
from execution.models.artifact import Artifact
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.execution_result import ExecutionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(year=2024, month=1, day=15, hour=10, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second)


# ---------------------------------------------------------------------------
# Shared ExecutionResult factories
# ---------------------------------------------------------------------------


@pytest.fixture()
def passed_result() -> ExecutionResult:
    """A minimal PASSED execution result with no artifacts or errors."""
    return ExecutionResult(
        run_id="run-pass-001",
        status=ExecutionStatus.PASSED,
        started_at=_utc(hour=10),
        completed_at=_utc(hour=10, minute=1, second=30),
    )


@pytest.fixture()
def failed_result() -> ExecutionResult:
    """A FAILED execution result with error message and stack trace."""
    return ExecutionResult(
        run_id="run-fail-002",
        status=ExecutionStatus.FAILED,
        started_at=_utc(hour=9),
        completed_at=_utc(hour=9, minute=0, second=45),
        error_message="AssertionError: Expected 'Submit' button to be visible.",
        stack_trace="Traceback (most recent call last):\n  File 'test.py', line 42\nAssertionError",
    )


@pytest.fixture()
def error_result() -> ExecutionResult:
    """An ERROR execution result with error message but no stack trace."""
    return ExecutionResult(
        run_id="run-err-003",
        status=ExecutionStatus.ERROR,
        started_at=_utc(hour=8),
        completed_at=_utc(hour=8, minute=0, second=5),
        error_message="Browser context closed unexpectedly.",
    )


@pytest.fixture()
def result_with_artifacts() -> ExecutionResult:
    """A PASSED result with screenshots, traces, and logs."""
    screenshot = Artifact(
        name="screenshot.png",
        path=Path("artifacts/screenshots/screenshot.png"),
        artifact_type=ArtifactType.SCREENSHOT,
        size_bytes=4096,
    )
    trace = Artifact(
        name="trace.zip",
        path=Path("artifacts/traces/trace.zip"),
        artifact_type=ArtifactType.TRACE,
        size_bytes=8192,
    )
    log = Artifact(
        name="execution.log",
        path=Path("artifacts/logs/execution.log"),
        artifact_type=ArtifactType.LOG,
        size_bytes=512,
    )
    bundle = ArtifactBundle(
        screenshots=[screenshot],
        traces=[trace],
        logs=[log],
    )
    return ExecutionResult(
        run_id="run-art-004",
        status=ExecutionStatus.PASSED,
        artifacts=bundle,
        started_at=_utc(hour=11),
        completed_at=_utc(hour=11, minute=2),
    )


@pytest.fixture()
def tmp_output_dir(tmp_path: Path) -> Path:
    """A temporary directory for writing report files."""
    out = tmp_path / "reports"
    out.mkdir(parents=True, exist_ok=True)
    return out
