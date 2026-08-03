"""
======================================================================

Module:
Markdown Report Generator

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Renders a ``Report`` as a GitHub-flavoured Markdown file.

The output is a UTF-8 encoded ``.md`` file suitable for:
- Committing to a repository as a test run artefact
- Displaying in GitHub PR checks
- Attaching to CI pipeline artifacts

Sections rendered
-----------------
- Summary       — status badge, run ID, timing table
- Error         — error message + fenced code block for stack trace
- Artifacts     — grouped tables of screenshots/traces/videos/logs
- Browser State — URL, title, viewport, cookies, storage
- Console Logs  — table with level + message
- Network       — requests, responses, failures tables
- DOM           — HTML size, text preview in fenced block

======================================================================
"""

from __future__ import annotations

from pathlib import Path

from reports.generators.base_generator import BaseGenerator
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

# Status emoji map for visual clarity in markdown
_STATUS_EMOJI = {
    "PASSED": "✅",
    "FAILED": "❌",
    "ERROR": "⚠️",
    "SKIPPED": "⏭️",
    "TIMEOUT": "⏱️",
    "CANCELLED": "🚫",
}


class MarkdownGenerator(BaseGenerator):
    """
    Renders a ``Report`` as a GitHub-flavoured Markdown file.
    """

    @property
    def format(self) -> str:
        return "markdown"

    def generate(self, report: Report, output_path: Path) -> Path:
        """
        Write *report* as Markdown to *output_path*.

        Parameters
        ----------
        report:
            Fully built ``Report`` object.
        output_path:
            Destination ``.md`` file path.

        Returns
        -------
        Path
            The path of the written file.
        """
        self._ensure_parent(output_path)
        md = self._render(report)
        output_path.write_text(md, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # Top-level rendering
    # ------------------------------------------------------------------

    def _render(self, report: Report) -> str:
        """Render the full Markdown document."""
        emoji = _STATUS_EMOJI.get(report.status, "🔵")
        lines: list[str] = [
            f"# {report.title}",
            "",
            f"> **Status:** {emoji} `{report.status}`  ",
            f"> **Run ID:** `{report.run_id}`  ",
            f"> **Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
        ]

        for section in report.sections:
            lines.extend(
                self._render_section(section.section_type, section.title, section.data)
            )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Section dispatcher
    # ------------------------------------------------------------------

    def _render_section(
        self, stype: SectionType, title: str, data: object
    ) -> list[str]:
        """Return lines for one section."""
        lines: list[str] = [f"## {title}", ""]
        if stype == SectionType.SUMMARY and isinstance(data, SummaryPayload):
            lines.extend(self._render_summary(data))
        elif stype == SectionType.ERROR and isinstance(data, ErrorPayload):
            lines.extend(self._render_error(data))
        elif stype == SectionType.ARTIFACTS and isinstance(data, ArtifactsPayload):
            lines.extend(self._render_artifacts(data))
        elif stype == SectionType.BROWSER_STATE and isinstance(data, BrowserStatePayload):
            lines.extend(self._render_browser_state(data))
        elif stype == SectionType.CONSOLE_LOGS and isinstance(data, ConsoleLogsPayload):
            lines.extend(self._render_console_logs(data))
        elif stype == SectionType.NETWORK and isinstance(data, NetworkPayload):
            lines.extend(self._render_network(data))
        elif stype == SectionType.DOM and isinstance(data, DOMPayload):
            lines.extend(self._render_dom(data))
        else:
            lines.append(f"_No renderer for section type: `{stype}`_")
        return lines

    # ------------------------------------------------------------------
    # Per-section renderers
    # ------------------------------------------------------------------

    def _render_summary(self, d: SummaryPayload) -> list[str]:
        emoji = _STATUS_EMOJI.get(d.status, "🔵")
        vp = f"{emoji} `{d.status}`"
        tags = ", ".join(d.tags) if d.tags else "—"
        rows = [
            ("Run ID", f"`{d.run_id}`"),
            ("Status", vp),
            ("Started", d.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Completed", d.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Duration", f"{d.duration_seconds:.2f}s"),
            ("Environment", d.environment or "—"),
            ("Browser", d.browser_type or "—"),
            ("Tags", tags),
        ]
        return self._kv_table(rows)

    def _render_error(self, d: ErrorPayload) -> list[str]:
        lines = [
            f"**Error:** {self._escape(d.error_message)}",
            "",
        ]
        if d.stack_trace:
            lines += [
                "<details>",
                "<summary>Stack Trace</summary>",
                "",
                "```",
                d.stack_trace,
                "```",
                "",
                "</details>",
            ]
        return lines

    def _render_artifacts(self, d: ArtifactsPayload) -> list[str]:
        if d.total == 0:
            return ["_No artifacts collected._"]
        lines: list[str] = []
        for group_name, items in [
            ("Screenshots", d.screenshots),
            ("Traces", d.traces),
            ("Videos", d.videos),
            ("Logs", d.logs),
        ]:
            if not items:
                continue
            lines.append(f"**{group_name}**")
            lines.append("")
            lines.append("| Name | Type | Path | Size |")
            lines.append("|------|------|------|------|")
            for a in items:
                lines.append(
                    f"| {self._escape(a.name)} "
                    f"| {self._escape(a.artifact_type)} "
                    f"| {self._escape(a.path)} "
                    f"| {a.size_bytes:,} bytes |"
                )
            lines.append("")
        return lines

    def _render_browser_state(self, d: BrowserStatePayload) -> list[str]:
        vp = (
            f"{d.viewport_width}×{d.viewport_height}"
            if d.viewport_width and d.viewport_height
            else "—"
        )
        ls_keys = ", ".join(d.local_storage_keys) if d.local_storage_keys else "—"
        ss_keys = ", ".join(d.session_storage_keys) if d.session_storage_keys else "—"
        rows = [
            ("URL", self._escape(d.current_url)),
            ("Title", self._escape(d.title) or "—"),
            ("User Agent", self._escape(d.user_agent) or "—"),
            ("Viewport", vp),
            ("Cookies", str(d.cookie_count)),
            ("localStorage keys", ls_keys),
            ("sessionStorage keys", ss_keys),
        ]
        return self._kv_table(rows)

    def _render_console_logs(self, d: ConsoleLogsPayload) -> list[str]:
        if not d.entries:
            return ["_No console messages captured._"]
        lines: list[str] = [
            f"**{len(d.entries)} messages** — "
            f"{d.error_count} errors, {d.warning_count} warnings",
            "",
            "| Level | Message |",
            "|-------|---------|",
        ]
        for entry in d.entries:
            lines.append(
                f"| `{self._escape(entry.level)}` | {self._escape(entry.message)} |"
            )
        return lines

    def _render_network(self, d: NetworkPayload) -> list[str]:
        lines: list[str] = []
        if d.requests:
            lines.append(f"**Requests ({len(d.requests)})**")
            lines.append("")
            lines.append("| Method | URL | Type |")
            lines.append("|--------|-----|------|")
            for r in d.requests:
                lines.append(
                    f"| `{self._escape(r.method)}` "
                    f"| {self._escape(r.url)} "
                    f"| {self._escape(r.resource_type)} |"
                )
            lines.append("")
        if d.responses:
            lines.append(f"**Responses ({len(d.responses)})**")
            lines.append("")
            lines.append("| URL | Status | Text |")
            lines.append("|-----|--------|------|")
            for r in d.responses:
                status_md = f"`{r.status_code}`"
                lines.append(
                    f"| {self._escape(r.url)} "
                    f"| {status_md} "
                    f"| {self._escape(r.status_text)} |"
                )
            lines.append("")
        if d.failures:
            lines.append(f"**⚠️ Failures ({len(d.failures)})**")
            lines.append("")
            lines.append("| Method | URL | Reason |")
            lines.append("|--------|-----|--------|")
            for f in d.failures:
                lines.append(
                    f"| `{self._escape(f.method)}` "
                    f"| {self._escape(f.url)} "
                    f"| {self._escape(f.failure_text)} |"
                )
            lines.append("")
        if not lines:
            lines.append("_No network events captured._")
        return lines

    def _render_dom(self, d: DOMPayload) -> list[str]:
        rows = [
            ("URL", self._escape(d.url)),
            ("HTML Size", f"{d.html_size_bytes:,} bytes"),
        ]
        lines = self._kv_table(rows)
        if d.text_preview:
            lines += [
                "",
                "**Text Preview**",
                "",
                "```",
                d.text_preview[:500],
                "```",
            ]
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _kv_table(rows: list[tuple[str, str]]) -> list[str]:
        """Render a two-column key/value markdown table."""
        lines = [
            "| Field | Value |",
            "|-------|-------|",
        ]
        for key, value in rows:
            lines.append(f"| **{key}** | {value} |")
        return lines

    @staticmethod
    def _escape(text: str) -> str:
        """
        Escape pipe characters in markdown table cells.

        Parameters
        ----------
        text:
            Raw text to escape.

        Returns
        -------
        str
        """
        return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", "")
