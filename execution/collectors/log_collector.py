"""
======================================================================

Module:
Log Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Captures browser console messages during execution.

Collected logs are converted into strongly typed LogEntry
objects and can later be attached to ExecutionResult,
reports and dashboards.

----------------------------------------------------------------------

TODO:
Support network failures and page exceptions.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by PlaywrightUIRunner.

======================================================================
"""

from playwright.sync_api import Page

from execution.models.log_entry import LogEntry


class LogCollector:
    """
    Collects browser console logs.
    """

    def __init__(self) -> None:

        self._logs: list[LogEntry] = []

    def attach(
        self,
        page: Page,
    ) -> None:
        """
        Register Playwright console listener.
        """

        page.on(
            "console",
            self._on_console_message,
        )

    def _on_console_message(
        self,
        message,
    ) -> None:
        """
        Handle console messages.
        """

        self._logs.append(
            LogEntry(
                level=message.type.upper(),
                source="Browser Console",
                message=message.text,
            )
        )

    def collect(
        self,
    ) -> list[LogEntry]:
        """
        Return collected logs.
        """

        return self._logs.copy()

    def clear(
        self,
    ) -> None:
        """
        Remove all stored logs.
        """

        self._logs.clear()