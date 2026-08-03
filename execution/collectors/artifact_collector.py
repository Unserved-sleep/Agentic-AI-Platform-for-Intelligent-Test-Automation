"""
======================================================================

Module:
Artifact Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Coordinates all execution artifact collectors.

This class serves as the single entry point for artifact
collection during and after execution.

Collectors integrated:
- ScreenshotCollector  — page screenshots
- TraceCollector       — Playwright trace archives
- VideoCollector       — screen recordings
- LogCollector         — execution log files
- ConsoleLogCollector  — browser console messages (Phase 6)
- NetworkCollector     — HTTP requests / responses / failures (Phase 6)

----------------------------------------------------------------------

TODO:
Support HAR file export.
Support download artifact collection.

----------------------------------------------------------------------

INTEGRATION:
Used by PlaywrightUIRunner, PlaywrightAPIRunner, and
BrowserExecutionAgent (MCP layer).

======================================================================
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from execution.collectors.log_collector import LogCollector
from execution.collectors.screenshot_collector import ScreenshotCollector
from execution.collectors.trace_collector import TraceCollector
from execution.collectors.video_collector import VideoCollector
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.browser_session import BrowserSession

if TYPE_CHECKING:
    from execution.collectors.console_log_collector import (
        ConsoleLogCollector,
    )
    from execution.collectors.network_collector import NetworkCollector


class ArtifactCollector:
    """
    Coordinates execution artifact collection.

    All six collector types are wired here.  ConsoleLogCollector
    and NetworkCollector are optional; pass ``None`` to disable
    them.

    Usage
    -----
    ::

        collector = ArtifactCollector(
            screenshot_collector=ScreenshotCollector(),
            trace_collector=TraceCollector(),
            video_collector=VideoCollector(),
            log_collector=LogCollector(),
            console_log_collector=ConsoleLogCollector(),
            network_collector=NetworkCollector(),
        )

        bundle = collector.collect(session=session)
    """

    def __init__(
        self,
        screenshot_collector: ScreenshotCollector,
        trace_collector: TraceCollector,
        video_collector: VideoCollector,
        log_collector: LogCollector,
        console_log_collector: Optional["ConsoleLogCollector"] = None,
        network_collector: Optional["NetworkCollector"] = None,
    ) -> None:
        """
        Initialize the ArtifactCollector.

        Parameters
        ----------
        screenshot_collector:
            Captures page screenshots.
        trace_collector:
            Saves Playwright trace archives.
        video_collector:
            Saves screen recordings.
        log_collector:
            Collects execution log files.
        console_log_collector:
            Collects browser console messages (optional).
            When ``None``, console_logs will be empty in
            the returned ArtifactBundle.
        network_collector:
            Captures HTTP network events (optional).
            When ``None``, network_events will be None in
            the returned ArtifactBundle.
        """

        self.screenshot_collector = screenshot_collector
        self.trace_collector = trace_collector
        self.video_collector = video_collector
        self.log_collector = log_collector
        self.console_log_collector = console_log_collector
        self.network_collector = network_collector

    def collect(
        self,
        session: BrowserSession,
    ) -> ArtifactBundle:
        """
        Collect all execution artifacts for *session*.

        Each collector is called in isolation; a failure in
        one collector does not prevent the others from running.

        Parameters
        ----------
        session:
            The active (or just-finished) BrowserSession.

        Returns
        -------
        ArtifactBundle
            All artifacts gathered for this execution.
        """

        bundle = ArtifactBundle()

        # ------------------------------------------------------------------
        # Screenshot
        # ------------------------------------------------------------------
        try:
            screenshot = self.screenshot_collector.collect(
                run_id=session.session_id,
                page=session.page,
            )
            bundle.screenshots.append(screenshot)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Trace
        # ------------------------------------------------------------------
        try:
            trace = self.trace_collector.collect(
                run_id=session.session_id,
            )
            bundle.traces.append(trace)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Video
        # ------------------------------------------------------------------
        try:
            video = self.video_collector.collect(
                session=session,
            )
            bundle.videos.append(video)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Log files
        # ------------------------------------------------------------------
        try:
            bundle.logs = self.log_collector.collect()
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Console logs (Phase 6)
        # ------------------------------------------------------------------
        if self.console_log_collector is not None:
            try:
                bundle.console_logs = (
                    self.console_log_collector.collect()
                )
            except Exception:
                pass

        # ------------------------------------------------------------------
        # Network events (Phase 6)
        # ------------------------------------------------------------------
        if self.network_collector is not None:
            try:
                bundle.network_events = (
                    self.network_collector.collect()
                )
            except Exception:
                pass

        return bundle
