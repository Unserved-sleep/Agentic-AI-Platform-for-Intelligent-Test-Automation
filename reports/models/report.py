"""
======================================================================

Module:
Report Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the top-level Report model that aggregates all
ReportSections for one execution run.

A Report is built by ReportBuilder from an ExecutionResult
and then passed to any generator (HTML, JSON, Markdown) for
export.

Fields
------
- run_id          — links back to the ExecutionResult
- status          — PASSED / FAILED / ERROR etc.
- title           — human-readable report title
- generated_at    — UTC timestamp when the report was built
- sections        — ordered list of ReportSection objects
- metadata        — arbitrary key/value tags

======================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from reports.models.report_section import ReportSection, SectionType


class Report(BaseModel):
    """
    Top-level execution report.

    Built by ``ReportBuilder`` from an ``ExecutionResult``.
    Passed to a generator (HTML / JSON / Markdown) for export.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    run_id: str = Field(
        ...,
        description="Execution run identifier this report belongs to.",
    )

    status: str = Field(
        ...,
        description="Final execution status string (e.g. 'PASSED', 'FAILED').",
    )

    title: str = Field(
        default="Execution Report",
        description="Human-readable report title.",
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this report was built.",
    )

    sections: list[ReportSection] = Field(
        default_factory=list,
        description="Ordered list of report sections.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key/value pairs (tags, environment, etc.).",
    )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def passed(self) -> bool:
        """True when status is PASSED."""
        return self.status == "PASSED"

    @property
    def failed(self) -> bool:
        """True when status is FAILED."""
        return self.status == "FAILED"

    def get_section(self, section_type: SectionType) -> Optional[ReportSection]:
        """
        Return the first section of *section_type*, or None.

        Parameters
        ----------
        section_type:
            The type of section to find.

        Returns
        -------
        ReportSection | None
        """
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None

    def get_all_sections(
        self, section_type: SectionType
    ) -> list[ReportSection]:
        """
        Return all sections of *section_type*.

        Parameters
        ----------
        section_type:
            The type of sections to collect.

        Returns
        -------
        list[ReportSection]
        """
        return [s for s in self.sections if s.section_type == section_type]
