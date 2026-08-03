"""
======================================================================

Module:
Report Builder

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Transforms an ``ExecutionResult`` into a fully structured
``Report`` model ready for export.

ReportBuilder is the single place where raw execution data
is interpreted and mapped to typed ``ReportSection`` payloads.
It does NOT write any files — that is the responsibility of
the generators (HTML, JSON, Markdown).

Sections built
--------------
1. Summary       — always present
2. Error         — only when error_message is set
3. Artifacts     — screenshots, traces, videos, logs
4. Browser State — when attached to execution metadata
5. Console Logs  — when console_logs is non-empty
6. Network       — when network_events is non-empty
7. DOM           — when a dom snapshot is available

Usage
-----
    builder = ReportBuilder()
    report  = builder.build(execution_result)

    # — or with optional enrichment data —
    report = builder.build(
        execution_result,
        browser_state=state,
        dom_snapshot=snapshot,
        title="My Test Run",
        environment="staging",
        tags=["smoke", "auth"],
    )

======================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from execution.models.execution_result import ExecutionResult
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.artifact import Artifact
from reports.models.report import Report
from reports.models.report_section import (
    ArtifactEntry,
    ArtifactsPayload,
    BrowserStatePayload,
    ConsoleLogEntry as ReportConsoleLogEntry,
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


class ReportBuilder:
    """
    Builds a ``Report`` from an ``ExecutionResult`` and optional
    enrichment data.

    This class is stateless — each ``build()`` call is independent.
    """

    def build(
        self,
        result: ExecutionResult,
        *,
        browser_state: Optional[Any] = None,
        dom_snapshot: Optional[Any] = None,
        title: str = "Execution Report",
        environment: str = "",
        browser_type: str = "",
        tags: Optional[list[str]] = None,
    ) -> Report:
        """
        Build a ``Report`` from an ``ExecutionResult``.

        Parameters
        ----------
        result:
            The completed execution result.
        browser_state:
            Optional ``BrowserState`` instance captured during
            execution. When provided, a Browser State section is
            included.
        dom_snapshot:
            Optional ``DOMSnapshot`` instance. When provided, a
            DOM section is included.
        title:
            Human-readable report title.
        environment:
            Optional environment tag (e.g. ``"staging"``).
        browser_type:
            Optional browser type label (e.g. ``"chromium"``).
        tags:
            Optional list of tags to attach to the summary.

        Returns
        -------
        Report
            Fully built, immutable report object.
        """
        sections: list[ReportSection] = []

        # 1. Summary — always present
        sections.append(
            self._build_summary_section(
                result=result,
                environment=environment,
                browser_type=browser_type,
                tags=tags or [],
            )
        )

        # 2. Error — only when there is an error message
        if result.error_message:
            sections.append(self._build_error_section(result))

        # 3. Artifacts
        sections.append(self._build_artifacts_section(result.artifacts))

        # 4. Browser State — optional
        if browser_state is not None:
            sections.append(self._build_browser_state_section(browser_state))

        # 5. Console Logs — when present in artifacts
        console_logs = getattr(result.artifacts, "console_logs", [])
        if console_logs:
            sections.append(self._build_console_logs_section(console_logs))

        # 6. Network — when network events present in artifacts
        network_events = getattr(result.artifacts, "network_events", None)
        if network_events is not None:
            sections.append(self._build_network_section(network_events))

        # 7. DOM — optional
        if dom_snapshot is not None:
            sections.append(self._build_dom_section(dom_snapshot))

        return Report(
            run_id=result.run_id,
            status=result.status.value
            if hasattr(result.status, "value")
            else str(result.status),
            title=title,
            generated_at=datetime.utcnow(),
            sections=sections,
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_summary_section(
        self,
        result: ExecutionResult,
        environment: str,
        browser_type: str,
        tags: list[str],
    ) -> ReportSection:
        """Build the execution summary section."""
        status_str = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        )
        duration = (
            (result.completed_at - result.started_at).total_seconds()
            if result.completed_at and result.started_at
            else 0.0
        )
        payload = SummaryPayload(
            run_id=result.run_id,
            status=status_str,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=duration,
            environment=environment,
            browser_type=browser_type,
            tags=tags,
        )
        return ReportSection(
            title="Summary",
            section_type=SectionType.SUMMARY,
            data=payload,
        )

    def _build_error_section(self, result: ExecutionResult) -> ReportSection:
        """Build the error section from result error fields."""
        payload = ErrorPayload(
            error_message=result.error_message or "Unknown error",
            stack_trace=result.stack_trace,
        )
        return ReportSection(
            title="Error",
            section_type=SectionType.ERROR,
            data=payload,
        )

    def _build_artifacts_section(self, bundle: ArtifactBundle) -> ReportSection:
        """Build the artifacts section from an ArtifactBundle."""
        payload = ArtifactsPayload(
            screenshots=self._convert_artifacts(bundle.screenshots),
            traces=self._convert_artifacts(bundle.traces),
            videos=self._convert_artifacts(bundle.videos),
            logs=self._convert_artifacts(bundle.logs),
        )
        return ReportSection(
            title="Artifacts",
            section_type=SectionType.ARTIFACTS,
            data=payload,
        )

    def _build_browser_state_section(self, browser_state: Any) -> ReportSection:
        """
        Build the browser state section from a ``BrowserState`` instance.

        Accepts any object with the BrowserState field names to
        avoid tight coupling to the execution module.
        """
        viewport = getattr(browser_state, "viewport", None)
        vp_width = getattr(viewport, "width", None) if viewport else None
        vp_height = getattr(viewport, "height", None) if viewport else None

        cookies: list = getattr(browser_state, "cookies", [])
        local_storage: dict = getattr(browser_state, "local_storage", {})
        session_storage: dict = getattr(browser_state, "session_storage", {})

        payload = BrowserStatePayload(
            current_url=getattr(browser_state, "current_url", ""),
            title=getattr(browser_state, "title", ""),
            user_agent=getattr(browser_state, "user_agent", ""),
            viewport_width=vp_width,
            viewport_height=vp_height,
            cookie_count=len(cookies),
            local_storage_keys=list(local_storage.keys()),
            session_storage_keys=list(session_storage.keys()),
        )
        return ReportSection(
            title="Browser State",
            section_type=SectionType.BROWSER_STATE,
            data=payload,
        )

    def _build_console_logs_section(self, raw_entries: list[Any]) -> ReportSection:
        """
        Build the console logs section.

        Each entry in *raw_entries* may be a ``ConsoleLogEntry``
        (from the execution collector) or any object with
        ``level``, ``message`` and optional ``timestamp`` fields.
        """
        entries: list[ReportConsoleLogEntry] = []
        for entry in raw_entries:
            level = self._get_attr(entry, "level", "INFO")
            message = self._get_attr(entry, "message", "")
            timestamp = self._get_attr(entry, "timestamp", None)
            entries.append(
                ReportConsoleLogEntry(
                    level=str(level).upper(),
                    message=str(message),
                    timestamp=timestamp,
                )
            )
        payload = ConsoleLogsPayload(entries=entries)
        return ReportSection(
            title="Console Logs",
            section_type=SectionType.CONSOLE_LOGS,
            data=payload,
        )

    def _build_network_section(self, network_events: Any) -> ReportSection:
        """
        Build the network section from a ``NetworkEventBundle``.

        Accepts any object with ``requests``, ``responses`` and
        ``failures`` lists.
        """
        raw_requests = self._get_attr(network_events, "requests", [])
        raw_responses = self._get_attr(network_events, "responses", [])
        raw_failures = self._get_attr(network_events, "failures", [])

        requests = [
            NetworkRequestEntry(
                method=str(self._get_attr(r, "method", "GET")),
                url=str(self._get_attr(r, "url", "")),
                resource_type=str(self._get_attr(r, "resource_type", "")),
            )
            for r in raw_requests
        ]
        responses = [
            NetworkResponseEntry(
                url=str(self._get_attr(r, "url", "")),
                status_code=int(self._get_attr(r, "status_code", 0)),
                status_text=str(self._get_attr(r, "status_text", "")),
                ok=bool(self._get_attr(r, "ok", False)),
            )
            for r in raw_responses
        ]
        failures = [
            NetworkFailureEntry(
                url=str(self._get_attr(f, "url", "")),
                method=str(self._get_attr(f, "method", "")),
                failure_text=str(self._get_attr(f, "failure_text", "")),
            )
            for f in raw_failures
        ]
        payload = NetworkPayload(
            requests=requests,
            responses=responses,
            failures=failures,
        )
        return ReportSection(
            title="Network",
            section_type=SectionType.NETWORK,
            data=payload,
        )

    def _build_dom_section(self, dom_snapshot: Any) -> ReportSection:
        """
        Build the DOM section from a ``DOMSnapshot`` instance.

        Accepts any object with ``url``, ``html`` and
        ``text_content`` fields.
        """
        html: str = str(self._get_attr(dom_snapshot, "html", ""))
        text_content: str = str(self._get_attr(dom_snapshot, "text_content", ""))
        payload = DOMPayload(
            url=str(self._get_attr(dom_snapshot, "url", "")),
            html_size_bytes=len(html.encode("utf-8")),
            text_preview=text_content[:500],
        )
        return ReportSection(
            title="DOM Snapshot",
            section_type=SectionType.DOM,
            data=payload,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_artifacts(artifacts: list[Artifact]) -> list[ArtifactEntry]:
        """
        Convert a list of ``Artifact`` objects to ``ArtifactEntry``
        report models.

        Parameters
        ----------
        artifacts:
            List of execution artifacts.

        Returns
        -------
        list[ArtifactEntry]
        """
        result: list[ArtifactEntry] = []
        for artifact in artifacts:
            artifact_type_str = (
                artifact.artifact_type.value
                if hasattr(artifact.artifact_type, "value")
                else str(artifact.artifact_type)
            )
            result.append(
                ArtifactEntry(
                    name=artifact.name,
                    artifact_type=artifact_type_str,
                    path=str(artifact.path),
                    size_bytes=artifact.size_bytes,
                )
            )
        return result

    @staticmethod
    def _get_attr(obj: Any, name: str, default: Any) -> Any:
        """
        Get *name* from *obj* using attribute or key lookup,
        falling back to *default*.

        Parameters
        ----------
        obj:
            Object or dict to query.
        name:
            Attribute / key name.
        default:
            Value to return when not found.

        Returns
        -------
        Any
        """
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)
