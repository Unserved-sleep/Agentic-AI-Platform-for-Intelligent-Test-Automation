"""
======================================================================

Module:
Base Generator (Abstract)

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the abstract contract every report generator must
implement.

A generator takes a ``Report`` and writes it to a file at
a given output path, returning a ``Path`` to the created
file.

All generators must implement:
- ``generate(report, output_path) -> Path``
- ``format`` property → ReportFormat enum value

======================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from reports.models.report import Report


class BaseGenerator(ABC):
    """
    Abstract base class for all report generators.

    Subclass and implement ``generate()`` to add a new export
    format.  The ``ReportBuilder`` selects generators by their
    ``format`` property.
    """

    @property
    @abstractmethod
    def format(self) -> str:
        """
        The format string this generator produces.

        Returns one of: ``"html"``, ``"json"``, ``"markdown"``.
        """

    @abstractmethod
    def generate(self, report: "Report", output_path: Path) -> Path:
        """
        Write *report* to *output_path* and return the path.

        Parameters
        ----------
        report:
            The fully built ``Report`` object.
        output_path:
            Destination file path.  Parent directories will be
            created if they do not exist.

        Returns
        -------
        Path
            The path of the written file (same as *output_path*).
        """

    # ------------------------------------------------------------------
    # Shared helpers available to all subclasses
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_parent(path: Path) -> None:
        """Create parent directories for *path* if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
