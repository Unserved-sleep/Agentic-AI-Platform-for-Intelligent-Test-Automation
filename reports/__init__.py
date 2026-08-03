"""
Reports package.

Provides the complete report generation pipeline for execution results:

- ``ReportBuilder``  — transforms ExecutionResult → Report model
- ``ReportAgent``    — orchestrates multi-format report export
- ``ReportOutput``   — dataclass returned by ReportAgent.generate()
- ``Report``         — the immutable report model
- All section types  — re-exported for convenience
"""

from reports.report_builder import ReportBuilder
from reports.report_agent import ReportAgent, ReportOutput
from reports.models.report import Report
from reports.models.report_section import (
    SectionType,
    ReportSection,
    SummaryPayload,
    ArtifactEntry,
    ArtifactsPayload,
    ConsoleLogEntry,
    ConsoleLogsPayload,
    NetworkRequestEntry,
    NetworkResponseEntry,
    NetworkFailureEntry,
    NetworkPayload,
    BrowserStatePayload,
    DOMPayload,
    ErrorPayload,
)
from reports.generators import (
    BaseGenerator,
    HTMLGenerator,
    JSONGenerator,
    MarkdownGenerator,
)

__all__ = [
    # Core pipeline
    "ReportBuilder",
    "ReportAgent",
    "ReportOutput",
    # Models
    "Report",
    "SectionType",
    "ReportSection",
    "SummaryPayload",
    "ArtifactEntry",
    "ArtifactsPayload",
    "ConsoleLogEntry",
    "ConsoleLogsPayload",
    "NetworkRequestEntry",
    "NetworkResponseEntry",
    "NetworkFailureEntry",
    "NetworkPayload",
    "BrowserStatePayload",
    "DOMPayload",
    "ErrorPayload",
    # Generators
    "BaseGenerator",
    "HTMLGenerator",
    "JSONGenerator",
    "MarkdownGenerator",
]
