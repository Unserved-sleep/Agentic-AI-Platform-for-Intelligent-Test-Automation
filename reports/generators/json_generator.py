"""
======================================================================

Module:
JSON Report Generator

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Renders a ``Report`` as a structured JSON file.

The output is a UTF-8 encoded JSON file with 2-space
indentation, suitable for programmatic consumption by
dashboards, CI pipelines, or downstream tooling.

All datetime values are serialised as ISO-8601 strings.
Enum values are serialised as their string value.

======================================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from reports.generators.base_generator import BaseGenerator
from reports.models.report import Report


def _default_serializer(obj: Any) -> Any:
    """
    Custom JSON serialiser for types not handled by the stdlib.

    Handles:
    - ``datetime``  → ISO-8601 string
    - ``Enum``      → enum value
    - ``Path``      → str
    - Pydantic models → their dict representation
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    # Pydantic v2 BaseModel
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JSONGenerator(BaseGenerator):
    """
    Renders a ``Report`` as a structured JSON file.

    The JSON structure mirrors the ``Report`` model with all
    nested sections serialised as plain dicts.
    """

    @property
    def format(self) -> str:
        return "json"

    def generate(self, report: Report, output_path: Path) -> Path:
        """
        Serialise *report* to JSON and write it to *output_path*.

        Parameters
        ----------
        report:
            Fully built ``Report`` object.
        output_path:
            Destination ``.json`` file path.

        Returns
        -------
        Path
            The path of the written file.
        """
        self._ensure_parent(output_path)
        payload = self._to_dict(report)
        json_text = json.dumps(payload, indent=2, default=_default_serializer)
        output_path.write_text(json_text, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def _to_dict(self, report: Report) -> dict:
        """
        Convert a ``Report`` to a plain dictionary suitable for JSON
        serialisation.

        Parameters
        ----------
        report:
            The report to convert.

        Returns
        -------
        dict
        """
        return {
            "run_id": report.run_id,
            "status": report.status,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "metadata": report.metadata,
            "sections": [
                {
                    "title": section.title,
                    "section_type": section.section_type.value
                    if isinstance(section.section_type, Enum)
                    else section.section_type,
                    "data": self._serialise_data(section.data),
                }
                for section in report.sections
            ],
        }

    def _serialise_data(self, data: Any) -> Any:
        """
        Recursively convert a section payload to a JSON-safe dict.

        Parameters
        ----------
        data:
            Section payload (Pydantic model or primitive).

        Returns
        -------
        Any
            JSON-safe value.
        """
        if data is None:
            return None

        # Pydantic v2
        if hasattr(data, "model_dump"):
            raw = data.model_dump()
            return self._clean_dict(raw)

        if isinstance(data, dict):
            return self._clean_dict(data)

        if isinstance(data, list):
            return [self._serialise_data(item) for item in data]

        if isinstance(data, datetime):
            return data.isoformat()

        if isinstance(data, Enum):
            return data.value

        if isinstance(data, Path):
            return str(data)

        return data

    def _clean_dict(self, d: dict) -> dict:
        """
        Walk a dict recursively, converting any non-serialisable
        values to safe types.

        Parameters
        ----------
        d:
            Dictionary to clean.

        Returns
        -------
        dict
        """
        result: dict = {}
        for key, value in d.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._clean_dict(value)
            elif isinstance(value, list):
                result[key] = [self._serialise_data(item) for item in value]
            elif hasattr(value, "model_dump"):
                result[key] = self._clean_dict(value.model_dump())
            else:
                result[key] = value
        return result
