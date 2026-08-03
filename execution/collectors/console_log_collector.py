"""
======================================================================

Module:
Console Log Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Collects browser console messages emitted during test
execution.

Console messages are captured for three severity levels:
- info  (console.log / console.info)
- warning (console.warn)
- error   (console.error)

Each captured entry includes:
- level     — "INFO", "WARNING", "ERROR", or the raw type
- message   — Text content of the console message
- timestamp — UTC time the message was recorded
- source    — Fixed string "browser:console"
- args      — Additional serialised arguments (when present)

Integration
-----------
ConsoleLogCollector is attached to a Playwright Page *before*
execution starts via the ``attach(page)`` method. Playwright
fires a ``console`` event for every message; the collector
registers a listener that converts each event into a
``ConsoleLogEntry``.

After execution, ``collect()`` returns all buffered entries.
``clear()`` resets the buffer so the collector can be
reused across tests.

----------------------------------------------------------------------

TODO:
Support page JavaScript error events separately.
Support ``pageerror`` event capture.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by ArtifactCollector.
Optionally injected into PlaywrightUIRunner and
PlaywrightAPIRunner via RunnerFactory.

======================================================================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Data model for a single console log entry
# ---------------------------------------------------------------------------


class ConsoleLogEntry(BaseModel):
    """
    A single browser console message.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC time the message was captured.",
    )

    level: str = Field(
        ...,
        description=(
            'Severity level: "INFO", "WARNING", "ERROR", '
            'or the raw Playwright console type string.'
        ),
    )

    message: str = Field(
        ...,
        description="Text content of the console message.",
    )

    source: str = Field(
        default="browser:console",
        description="Origin of the log entry.",
    )

    args: list[str] = Field(
        default_factory=list,
        description="Serialised additional arguments.",
    )


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


# Map from Playwright console type strings to normalised levels.
_LEVEL_MAP: dict[str, str] = {
    "log": "INFO",
    "info": "INFO",
    "debug": "INFO",
    "warning": "WARNING",
    "warn": "WARNING",
    "error": "ERROR",
}


class ConsoleLogCollector:
    """
    Listens to Playwright browser console events and buffers
    them as ``ConsoleLogEntry`` objects.

    Typical usage
    -------------
    ::

        collector = ConsoleLogCollector()

        # Before test execution
        collector.attach(page)

        # … run the test …

        # After test execution
        entries = collector.collect()   # list[ConsoleLogEntry]

        # Reset for next test
        collector.clear()
    """

    def __init__(self) -> None:
        self._entries: list[ConsoleLogEntry] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def attach(self, page: Any) -> None:
        """
        Register a Playwright console listener on *page*.

        This method must be called before the test function
        starts so that all messages are captured.

        Parameters
        ----------
        page:
            An active ``playwright.sync_api.Page`` instance.
        """
        page.on("console", self._on_console_message)

    # ------------------------------------------------------------------
    # Internal handler
    # ------------------------------------------------------------------

    def _on_console_message(self, message: Any) -> None:
        """
        Handle a single Playwright ConsoleMessage event.

        Parameters
        ----------
        message:
            Playwright ConsoleMessage object.
        """
        raw_type: str = getattr(message, "type", "log")
        level = _LEVEL_MAP.get(raw_type.lower(), raw_type.upper())

        # Serialise extra args when present.
        try:
            args = [str(a) for a in message.args]
        except Exception:
            args = []

        entry = ConsoleLogEntry(
            level=level,
            message=message.text,
            args=args,
        )

        self._entries.append(entry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(self) -> list[ConsoleLogEntry]:
        """
        Return a copy of all captured console log entries.

        Returns
        -------
        list[ConsoleLogEntry]
        """
        return list(self._entries)

    def collect_by_level(self, level: str) -> list[ConsoleLogEntry]:
        """
        Return only entries whose level matches *level*
        (case-insensitive).

        Parameters
        ----------
        level:
            "INFO", "WARNING", or "ERROR".

        Returns
        -------
        list[ConsoleLogEntry]
        """
        target = level.upper()
        return [e for e in self._entries if e.level == target]

    def has_errors(self) -> bool:
        """
        Return True if any ERROR-level entry was captured.

        Returns
        -------
        bool
        """
        return any(e.level == "ERROR" for e in self._entries)

    def has_warnings(self) -> bool:
        """
        Return True if any WARNING-level entry was captured.

        Returns
        -------
        bool
        """
        return any(e.level == "WARNING" for e in self._entries)

    def clear(self) -> None:
        """
        Remove all buffered log entries.
        """
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
