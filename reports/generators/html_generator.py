"""
======================================================================

Module:
HTML Report Generator

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Renders a ``Report`` as a self-contained HTML file.

Uses only Python stdlib (no Jinja2 dependency) so the report
package has zero additional requirements.

The output is a single .html file with inline CSS that
renders cleanly in any modern browser.

Sections rendered
-----------------
- Summary       — status badge, run ID, timing
- Error         — error message + collapsible stack trace
- Artifacts     — grouped tables of screenshots/traces/videos/logs
- Browser State — URL, title, viewport, cookies, storage
- Console Logs  — colour-coded by level (INFO/WARNING/ERROR)
- Network       — requests, responses, failures tables
- DOM           — HTML size, text preview

======================================================================
"""

from __future__ import annotations

from pathlib import Path
from html import escape

from reports.generators.base_generator import BaseGenerator
from reports.models.report import Report
from reports.models.report_section import (
    SectionType,
    SummaryPayload,
    ArtifactsPayload,
    ConsoleLogsPayload,
    NetworkPayload,
    BrowserStatePayload,
    DOMPayload,
    ErrorPayload,
)


_CSS = """
body{font-family:Arial,sans-serif;margin:0;padding:0;background:#f5f5f5;color:#333}
header{background:#1a1a2e;color:#fff;padding:20px 32px}
header h1{margin:0;font-size:1.4rem}
header .meta{font-size:.85rem;opacity:.8;margin-top:4px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-weight:bold;font-size:.85rem}
.PASSED{background:#d4edda;color:#155724}
.FAILED{background:#f8d7da;color:#721c24}
.ERROR{background:#fff3cd;color:#856404}
main{max-width:1100px;margin:24px auto;padding:0 16px}
section{background:#fff;border-radius:8px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.1)}
section h2{margin:0;padding:14px 20px;border-bottom:1px solid #eee;font-size:1rem;color:#1a1a2e}
.content{padding:16px 20px}
table{width:100%;border-collapse:collapse;font-size:.87rem}
th{background:#f0f0f5;text-align:left;padding:7px 10px;font-weight:600}
td{padding:7px 10px;border-bottom:1px solid #f0f0f0;word-break:break-all}
tr:last-child td{border-bottom:none}
.level-INFO{color:#0c5460}
.level-WARNING{color:#856404}
.level-ERROR{color:#721c24;font-weight:bold}
pre{background:#f8f8f8;border:1px solid #ddd;border-radius:4px;padding:12px;overflow-x:auto;font-size:.82rem;white-space:pre-wrap}
details summary{cursor:pointer;font-weight:600;padding:4px 0}
.stat{display:inline-block;margin-right:24px}
.stat .label{font-size:.75rem;color:#666;display:block}
.stat .value{font-size:1.1rem;font-weight:bold}
""".strip()


class HTMLGenerator(BaseGenerator):
    """Renders a Report as a self-contained HTML file."""

    @property
    def format(self) -> str:
        return "html"

    def generate(self, report: Report, output_path: Path) -> Path:
        self._ensure_parent(output_path)
        html = self._render(report)
        output_path.write_text(html, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, report: Report) -> str:
        badge_class = report.status if report.status in ("PASSED", "FAILED") else "ERROR"
        title = escape(report.title)
        parts = [
            f"<!DOCTYPE html><html lang='en'><head>",
            f"<meta charset='UTF-8'>",
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>",
            f"<title>{title}</title>",
            f"<style>{_CSS}</style>",
            f"</head><body>",
            f"<header>",
            f"  <h1>{title} "
            f"<span class='badge {badge_class}'>{escape(report.status)}</span></h1>",
            f"  <div class='meta'>Run ID: {escape(report.run_id)} &nbsp;|&nbsp; "
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</div>",
            f"</header><main>",
        ]

        for section in report.sections:
            parts.append(self._render_section(section.section_type, section.title, section.data))

        parts += ["</main></body></html>"]
        return "\n".join(parts)

    def _render_section(self, stype: SectionType, title: str, data: object) -> str:
        body = ""
        if stype == SectionType.SUMMARY and isinstance(data, SummaryPayload):
            body = self._render_summary(data)
        elif stype == SectionType.ERROR and isinstance(data, ErrorPayload):
            body = self._render_error(data)
        elif stype == SectionType.ARTIFACTS and isinstance(data, ArtifactsPayload):
            body = self._render_artifacts(data)
        elif stype == SectionType.BROWSER_STATE and isinstance(data, BrowserStatePayload):
            body = self._render_browser_state(data)
        elif stype == SectionType.CONSOLE_LOGS and isinstance(data, ConsoleLogsPayload):
            body = self._render_console_logs(data)
        elif stype == SectionType.NETWORK and isinstance(data, NetworkPayload):
            body = self._render_network(data)
        elif stype == SectionType.DOM and isinstance(data, DOMPayload):
            body = self._render_dom(data)
        else:
            body = f"<p><em>No renderer for section type: {stype}</em></p>"

        return (
            f"<section>"
            f"<h2>{escape(title)}</h2>"
            f"<div class='content'>{body}</div>"
            f"</section>"
        )

    def _render_summary(self, d: SummaryPayload) -> str:
        badge = d.status if d.status in ("PASSED", "FAILED") else "ERROR"
        rows = [
            ("Run ID", d.run_id),
            ("Status", f"<span class='badge {badge}'>{escape(d.status)}</span>"),
            ("Started", d.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Completed", d.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Duration", f"{d.duration_seconds:.2f}s"),
            ("Environment", d.environment or "—"),
            ("Browser", d.browser_type or "—"),
            ("Tags", ", ".join(d.tags) or "—"),
        ]
        cells = "".join(
            f"<tr><th style='width:160px'>{escape(k)}</th><td>{v}</td></tr>"
            for k, v in rows
        )
        return f"<table>{cells}</table>"

    def _render_error(self, d: ErrorPayload) -> str:
        msg = f"<p><strong>{escape(d.error_message)}</strong></p>"
        if d.stack_trace:
            msg += (
                f"<details><summary>Stack Trace</summary>"
                f"<pre>{escape(d.stack_trace)}</pre></details>"
            )
        return msg

    def _render_artifacts(self, d: ArtifactsPayload) -> str:
        if d.total == 0:
            return "<p><em>No artifacts collected.</em></p>"
        parts = []
        for group_name, items in [
            ("Screenshots", d.screenshots),
            ("Traces", d.traces),
            ("Videos", d.videos),
            ("Logs", d.logs),
        ]:
            if not items:
                continue
            rows = "".join(
                f"<tr><td>{escape(a.name)}</td>"
                f"<td>{escape(a.artifact_type)}</td>"
                f"<td>{escape(a.path)}</td>"
                f"<td>{a.size_bytes:,}</td></tr>"
                for a in items
            )
            parts.append(
                f"<p><strong>{group_name}</strong></p>"
                f"<table><tr><th>Name</th><th>Type</th><th>Path</th><th>Size (bytes)</th></tr>"
                f"{rows}</table>"
            )
        return "".join(parts)

    def _render_browser_state(self, d: BrowserStatePayload) -> str:
        vp = (
            f"{d.viewport_width}×{d.viewport_height}"
            if d.viewport_width and d.viewport_height
            else "—"
        )
        rows = [
            ("URL", escape(d.current_url)),
            ("Title", escape(d.title) or "—"),
            ("User Agent", escape(d.user_agent) or "—"),
            ("Viewport", vp),
            ("Cookies", str(d.cookie_count)),
            ("localStorage keys", ", ".join(d.local_storage_keys) or "—"),
            ("sessionStorage keys", ", ".join(d.session_storage_keys) or "—"),
        ]
        cells = "".join(
            f"<tr><th style='width:180px'>{k}</th><td>{v}</td></tr>"
            for k, v in rows
        )
        return f"<table>{cells}</table>"

    def _render_console_logs(self, d: ConsoleLogsPayload) -> str:
        if not d.entries:
            return "<p><em>No console messages captured.</em></p>"
        rows = "".join(
            f"<tr><td class='level-{escape(e.level)}'>{escape(e.level)}</td>"
            f"<td>{escape(e.message)}</td></tr>"
            for e in d.entries
        )
        return (
            f"<p>{len(d.entries)} messages — "
            f"{d.error_count} errors, {d.warning_count} warnings</p>"
            f"<table><tr><th>Level</th><th>Message</th></tr>{rows}</table>"
        )

    def _render_network(self, d: NetworkPayload) -> str:
        parts = []
        if d.requests:
            rows = "".join(
                f"<tr><td>{escape(r.method)}</td><td>{escape(r.url)}</td>"
                f"<td>{escape(r.resource_type)}</td></tr>"
                for r in d.requests
            )
            parts.append(
                f"<p><strong>Requests ({len(d.requests)})</strong></p>"
                f"<table><tr><th>Method</th><th>URL</th><th>Type</th></tr>{rows}</table>"
            )
        if d.responses:
            rows = "".join(
                f"<tr><td>{escape(r.url)}</td>"
                f"<td style='color:{'green' if r.ok else 'red'}'>{r.status_code}</td>"
                f"<td>{escape(r.status_text)}</td></tr>"
                for r in d.responses
            )
            parts.append(
                f"<p><strong>Responses ({len(d.responses)})</strong></p>"
                f"<table><tr><th>URL</th><th>Status</th><th>Text</th></tr>{rows}</table>"
            )
        if d.failures:
            rows = "".join(
                f"<tr><td>{escape(f.method)}</td><td>{escape(f.url)}</td>"
                f"<td>{escape(f.failure_text)}</td></tr>"
                for f in d.failures
            )
            parts.append(
                f"<p><strong style='color:red'>Failures ({len(d.failures)})</strong></p>"
                f"<table><tr><th>Method</th><th>URL</th><th>Reason</th></tr>{rows}</table>"
            )
        return "".join(parts) or "<p><em>No network events captured.</em></p>"

    def _render_dom(self, d: DOMPayload) -> str:
        preview = escape(d.text_preview[:500]) if d.text_preview else "—"
        rows = [
            ("URL", escape(d.url)),
            ("HTML size", f"{d.html_size_bytes:,} bytes"),
            ("Text preview", f"<pre>{preview}</pre>"),
        ]
        cells = "".join(
            f"<tr><th style='width:140px'>{k}</th><td>{v}</td></tr>"
            for k, v in rows
        )
        return f"<table>{cells}</table>"
