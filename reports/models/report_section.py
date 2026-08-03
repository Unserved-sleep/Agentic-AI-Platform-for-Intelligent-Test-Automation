"""
======================================================================

Module:
Report Section Models

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the granular data models that make up individual
sections of an execution report.

Sections are composable units. A Report is an ordered list
of ReportSections. Each section has a title, a type, and a
typed payload.

Section types
-------------
- SummarySection       — pass/fail, timing, run metadata
- ArtifactSection      — screenshots, traces, videos, logs
- ConsoleLogSection    — browser console messages
- NetworkSection       — HTTP requests / responses / failures
- BrowserStateSection  — URL, title, cookies, storage, viewport
- DOMSection           — HTML + text content snapshot
- ErrorSection         — error message + stack trace

All models are frozen Pydantic BaseModels so they can be
safely cached and compared.

======================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# SectionType enum
# ---------------------------------------------------------------------------


class SectionType(str, Enum):
    """Identifies the kind of data a ReportSection carries."""

    SUMMARY = "summary"
    ARTIFACTS = "artifacts"
    CONSOLE_LOGS = "console_logs"
    NETWORK = "network"
    BROWSER_STATE = "browser_state"
    DOM = "dom"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Section payload models
# ---------------------------------------------------------------------------


class SummaryPayload(BaseModel):
    """Execution summary data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    environment: str = ""
    tags: list[str] = Field(default_factory=list)
    browser_type: str = ""


class ArtifactEntry(BaseModel):
    """A single artifact reference inside an ArtifactsPayload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    artifact_type: str
    path: str          # string so JSON/HTML rendering is simple
    size_bytes: int = 0


class ArtifactsPayload(BaseModel):
    """All execution artifacts grouped by type."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    screenshots: list[ArtifactEntry] = Field(default_factory=list)
    traces: list[ArtifactEntry] = Field(default_factory=list)
    videos: list[ArtifactEntry] = Field(default_factory=list)
    logs: list[ArtifactEntry] = Field(default_factory=list)

    @property
    def total(self) -> int:
        return (
            len(self.screenshots)
            + len(self.traces)
            + len(self.videos)
            + len(self.logs)
        )


class ConsoleLogEntry(BaseModel):
    """A single console log line for reporting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: str
    message: str
    timestamp: Optional[datetime] = None


class ConsoleLogsPayload(BaseModel):
    """All captured console log entries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: list[ConsoleLogEntry] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.entries if e.level == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.entries if e.level == "WARNING")


class NetworkRequestEntry(BaseModel):
    """A single network request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: str
    url: str
    resource_type: str = ""


class NetworkResponseEntry(BaseModel):
    """A single network response."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    status_code: int
    status_text: str = ""
    ok: bool


class NetworkFailureEntry(BaseModel):
    """A single failed network request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    method: str = ""
    failure_text: str = ""


class NetworkPayload(BaseModel):
    """All captured network events."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requests: list[NetworkRequestEntry] = Field(default_factory=list)
    responses: list[NetworkResponseEntry] = Field(default_factory=list)
    failures: list[NetworkFailureEntry] = Field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return len(self.failures) > 0


class BrowserStatePayload(BaseModel):
    """Key browser state fields for the report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    current_url: str
    title: str = ""
    user_agent: str = ""
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    cookie_count: int = 0
    local_storage_keys: list[str] = Field(default_factory=list)
    session_storage_keys: list[str] = Field(default_factory=list)


class DOMPayload(BaseModel):
    """DOM snapshot summary for the report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    html_size_bytes: int = 0
    text_preview: str = ""    # first 500 chars of text_content


class ErrorPayload(BaseModel):
    """Error details for a failed execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    error_message: str
    stack_trace: Optional[str] = None


# ---------------------------------------------------------------------------
# Union type for section data
# ---------------------------------------------------------------------------

SectionPayload = (
    SummaryPayload
    | ArtifactsPayload
    | ConsoleLogsPayload
    | NetworkPayload
    | BrowserStatePayload
    | DOMPayload
    | ErrorPayload
)


# ---------------------------------------------------------------------------
# ReportSection
# ---------------------------------------------------------------------------


class ReportSection(BaseModel):
    """
    A single titled section of a report.

    Each section has a ``section_type`` that identifies the
    kind of data it carries and a ``data`` payload of the
    matching type.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    title: str = Field(..., description="Human-readable section heading.")
    section_type: SectionType
    data: Any = Field(..., description="Typed payload for this section.")
