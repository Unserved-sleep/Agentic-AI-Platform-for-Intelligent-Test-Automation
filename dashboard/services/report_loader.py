"""
dashboard/services/report_loader.py
=====================================
Loads JSON reports produced by ReportAgent from disk.

Reports are written to artifacts/reports/<run_id>.json by JSONGenerator.
This service scans that directory, parses the files, and returns
plain dicts — no dependency on the execution or reports packages.

The dashboard is a read-only consumer of already-generated reports.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default report directory relative to project root
_DEFAULT_REPORT_DIR = Path("artifacts") / "reports"


class ReportLoader:
    """
    Scans a directory for JSON reports and exposes them as dicts.

    Parameters
    ----------
    report_dir:
        Directory that contains ``<run_id>.json`` report files.
        Defaults to ``artifacts/reports``.
    """

    def __init__(self, report_dir: Optional[Path] = None) -> None:
        self.report_dir = report_dir or _DEFAULT_REPORT_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_reports(self) -> list[dict[str, Any]]:
        """
        Return all valid reports sorted newest-first.

        Each entry is the parsed JSON dict.  Malformed or unreadable
        files are logged and skipped.

        Returns
        -------
        list[dict]
            Reports ordered by ``generated_at`` descending.
        """
        if not self.report_dir.exists():
            logger.warning("Report directory does not exist: %s", self.report_dir)
            return []

        reports: list[dict[str, Any]] = []
        for path in self.report_dir.glob("*.json"):
            report = self._load_file(path)
            if report is not None:
                reports.append(report)

        reports.sort(
            key=lambda r: r.get("generated_at", ""),
            reverse=True,
        )
        return reports

    def load_report(self, run_id: str) -> Optional[dict[str, Any]]:
        """
        Load a single report by run_id.

        Parameters
        ----------
        run_id:
            The execution run identifier.

        Returns
        -------
        dict | None
            Parsed report dict, or None if not found.
        """
        path = self.report_dir / f"{run_id}.json"
        if not path.exists():
            logger.warning("Report file not found: %s", path)
            return None
        return self._load_file(path)

    def get_summary_rows(self) -> list[dict[str, Any]]:
        """
        Return a flattened list of summary rows for table display.

        Each row contains: run_id, status, title, generated_at,
        duration_seconds, environment, browser_type.

        Returns
        -------
        list[dict]
        """
        rows = []
        for report in self.list_reports():
            row = {
                "run_id": report.get("run_id", ""),
                "status": report.get("status", ""),
                "title": report.get("title", ""),
                "generated_at": report.get("generated_at", ""),
            }
            # Extract summary section data if present
            for section in report.get("sections", []):
                if section.get("section_type") == "summary":
                    data = section.get("data", {})
                    row["duration_seconds"] = data.get("duration_seconds", 0.0)
                    row["environment"] = data.get("environment", "")
                    row["browser_type"] = data.get("browser_type", "")
                    break
            else:
                row.setdefault("duration_seconds", 0.0)
                row.setdefault("environment", "")
                row.setdefault("browser_type", "")
            rows.append(row)
        return rows

    # ------------------------------------------------------------------
    # Statistics helpers (used by Home and Analytics pages)
    # ------------------------------------------------------------------

    def compute_stats(self) -> dict[str, Any]:
        """
        Compute aggregate statistics across all reports.

        Returns
        -------
        dict with keys:
            total, passed, failed, error, pass_rate,
            avg_duration_seconds
        """
        reports = self.list_reports()
        total = len(reports)
        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "error": 0,
                "pass_rate": 0.0,
                "avg_duration_seconds": 0.0,
            }

        passed = sum(1 for r in reports if r.get("status") == "PASSED")
        failed = sum(1 for r in reports if r.get("status") == "FAILED")
        error = total - passed - failed

        durations: list[float] = []
        for r in reports:
            for section in r.get("sections", []):
                if section.get("section_type") == "summary":
                    d = section.get("data", {}).get("duration_seconds")
                    if isinstance(d, (int, float)):
                        durations.append(float(d))
                    break

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "pass_rate": round(passed / total * 100, 1) if total else 0.0,
            "avg_duration_seconds": round(avg_duration, 2),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_file(self, path: Path) -> Optional[dict[str, Any]]:
        """Parse a single JSON report file, returning None on error."""
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            if not isinstance(data, dict):
                logger.warning("Unexpected JSON structure in %s", path)
                return None
            return data
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load report %s: %s", path, exc)
            return None
