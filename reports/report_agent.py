"""
======================================================================

Module:
Report Agent

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
High-level agent that orchestrates the full report generation
pipeline for an ``ExecutionResult``.

ReportAgent ties together ``ReportBuilder`` and the format
generators (HTML, JSON, Markdown) so callers need only supply
an ``ExecutionResult`` and optional output settings.

Public API
----------
``generate(result, formats, output_dir, **kwargs) -> ReportOutput``

    Build a ``Report`` from *result*, then write one file for
    each requested format, and return a ``ReportOutput`` that
    contains all generated file paths.

``generate_html(result, output_path, **kwargs) -> Path``
``generate_json(result, output_path, **kwargs) -> Path``
``generate_markdown(result, output_path, **kwargs) -> Path``

    Convenience methods for single-format export.

Supported formats
-----------------
- ``"html"``     → HTMLGenerator
- ``"json"``     → JSONGenerator
- ``"markdown"`` → MarkdownGenerator

Usage
-----
    from reports.report_agent import ReportAgent
    from execution.models.execution_result import ExecutionResult

    agent  = ReportAgent()
    output = agent.generate(result, formats=["html", "json"])
    print(output.html_path)   # Path to the generated HTML
    print(output.json_path)   # Path to the generated JSON

======================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from execution.models.execution_result import ExecutionResult
from reports.generators.html_generator import HTMLGenerator
from reports.generators.json_generator import JSONGenerator
from reports.generators.markdown_generator import MarkdownGenerator
from reports.models.report import Report
from reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)

# Default output directory for reports
_DEFAULT_OUTPUT_DIR = Path("artifacts") / "reports"


@dataclass
class ReportOutput:
    """
    Result of a ``ReportAgent.generate()`` call.

    Contains the ``Report`` model and all generated file paths
    keyed by format name.
    """

    report: Report
    """The built ``Report`` model."""

    paths: dict[str, Path] = field(default_factory=dict)
    """Map of format name → output file path."""

    @property
    def html_path(self) -> Optional[Path]:
        """Path to the generated HTML report, or None."""
        return self.paths.get("html")

    @property
    def json_path(self) -> Optional[Path]:
        """Path to the generated JSON report, or None."""
        return self.paths.get("json")

    @property
    def markdown_path(self) -> Optional[Path]:
        """Path to the generated Markdown report, or None."""
        return self.paths.get("markdown")


class ReportAgent:
    """
    Orchestrates end-to-end report generation.

    Takes an ``ExecutionResult``, builds a ``Report``, then
    writes files in the requested formats.

    Parameters
    ----------
    output_dir:
        Default output directory when no explicit path is
        supplied. Defaults to ``artifacts/reports``.
    builder:
        Optional custom ``ReportBuilder`` instance. If not
        supplied, a default instance is created.
    """

    _GENERATORS = {
        "html": HTMLGenerator,
        "json": JSONGenerator,
        "markdown": MarkdownGenerator,
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        builder: Optional[ReportBuilder] = None,
    ) -> None:
        self._output_dir = output_dir or _DEFAULT_OUTPUT_DIR
        self._builder = builder or ReportBuilder()

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def generate(
        self,
        result: ExecutionResult,
        formats: Optional[list[str]] = None,
        output_dir: Optional[Path] = None,
        *,
        browser_state: Optional[Any] = None,
        dom_snapshot: Optional[Any] = None,
        title: str = "Execution Report",
        environment: str = "",
        browser_type: str = "",
        tags: Optional[list[str]] = None,
    ) -> ReportOutput:
        """
        Build a report and export it in all requested formats.

        Parameters
        ----------
        result:
            Completed ``ExecutionResult``.
        formats:
            List of format strings. Supported: ``"html"``,
            ``"json"``, ``"markdown"``. Defaults to
            ``["html", "json", "markdown"]``.
        output_dir:
            Directory to write files into.  Defaults to the
            directory supplied at construction time.
        browser_state:
            Optional ``BrowserState`` for enrichment.
        dom_snapshot:
            Optional ``DOMSnapshot`` for enrichment.
        title:
            Report title.
        environment:
            Environment label (e.g. ``"staging"``).
        browser_type:
            Browser type label (e.g. ``"chromium"``).
        tags:
            List of string tags.

        Returns
        -------
        ReportOutput
            Contains the ``Report`` model and all generated paths.

        Raises
        ------
        ValueError
            If an unsupported format is requested.
        """
        formats = formats or ["html", "json", "markdown"]
        base_dir = output_dir or self._output_dir

        # Validate formats before building anything
        unsupported = [f for f in formats if f not in self._GENERATORS]
        if unsupported:
            raise ValueError(
                f"Unsupported report format(s): {unsupported}. "
                f"Supported: {list(self._GENERATORS.keys())}"
            )

        # Build the Report model once
        report = self._builder.build(
            result,
            browser_state=browser_state,
            dom_snapshot=dom_snapshot,
            title=title,
            environment=environment,
            browser_type=browser_type,
            tags=tags,
        )

        # Generate each requested format
        generated: dict[str, Path] = {}
        for fmt in formats:
            generator_cls = self._GENERATORS[fmt]
            generator = generator_cls()
            ext = self._extension(fmt)
            output_path = base_dir / f"{result.run_id}.{ext}"
            try:
                generated_path = generator.generate(report, output_path)
                generated[fmt] = generated_path
                logger.info(
                    "Report generated: format=%s path=%s",
                    fmt,
                    generated_path,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to generate %s report for run_id=%s: %s",
                    fmt,
                    result.run_id,
                    exc,
                    exc_info=True,
                )
                raise

        return ReportOutput(report=report, paths=generated)

    # ------------------------------------------------------------------
    # Single-format convenience methods
    # ------------------------------------------------------------------

    def generate_html(
        self,
        result: ExecutionResult,
        output_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Path:
        """
        Generate an HTML report and return the output path.

        Parameters
        ----------
        result:
            Completed ``ExecutionResult``.
        output_path:
            Explicit destination path. When None, a default path
            under the output directory is used.
        **kwargs:
            Forwarded to ``generate()`` (title, environment, etc.).

        Returns
        -------
        Path
        """
        output_path = output_path or (
            self._output_dir / f"{result.run_id}.html"
        )
        report = self._builder.build(result, **kwargs)
        return HTMLGenerator().generate(report, output_path)

    def generate_json(
        self,
        result: ExecutionResult,
        output_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Path:
        """
        Generate a JSON report and return the output path.

        Parameters
        ----------
        result:
            Completed ``ExecutionResult``.
        output_path:
            Explicit destination path. When None, a default path
            under the output directory is used.
        **kwargs:
            Forwarded to ``generate()`` (title, environment, etc.).

        Returns
        -------
        Path
        """
        output_path = output_path or (
            self._output_dir / f"{result.run_id}.json"
        )
        report = self._builder.build(result, **kwargs)
        return JSONGenerator().generate(report, output_path)

    def generate_markdown(
        self,
        result: ExecutionResult,
        output_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> Path:
        """
        Generate a Markdown report and return the output path.

        Parameters
        ----------
        result:
            Completed ``ExecutionResult``.
        output_path:
            Explicit destination path. When None, a default path
            under the output directory is used.
        **kwargs:
            Forwarded to ``generate()`` (title, environment, etc.).

        Returns
        -------
        Path
        """
        output_path = output_path or (
            self._output_dir / f"{result.run_id}.md"
        )
        report = self._builder.build(result, **kwargs)
        return MarkdownGenerator().generate(report, output_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extension(fmt: str) -> str:
        """
        Return the file extension for *fmt*.

        Parameters
        ----------
        fmt:
            Format string (``"html"``, ``"json"``, ``"markdown"``).

        Returns
        -------
        str
            File extension without leading dot.
        """
        _ext_map = {
            "html": "html",
            "json": "json",
            "markdown": "md",
        }
        return _ext_map.get(fmt, fmt)
