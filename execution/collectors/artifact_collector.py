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

----------------------------------------------------------------------

TODO:
Support future artifact collectors (HAR, downloads, etc.).

----------------------------------------------------------------------

INTEGRATION:
Used by PlaywrightUIRunner.

======================================================================
"""

from execution.collectors.log_collector import LogCollector
from execution.collectors.screenshot_collector import ScreenshotCollector
from execution.collectors.trace_collector import TraceCollector
from execution.collectors.video_collector import VideoCollector
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.browser_session import BrowserSession


class ArtifactCollector:
    """
    Coordinates execution artifact collection.
    """

    def __init__(
        self,
        screenshot_collector: ScreenshotCollector,
        trace_collector: TraceCollector,
        video_collector: VideoCollector,
        log_collector: LogCollector,
    ) -> None:

        self.screenshot_collector = screenshot_collector
        self.trace_collector = trace_collector
        self.video_collector = video_collector
        self.log_collector = log_collector

    def collect(
        self,
        session: BrowserSession,
    ) -> ArtifactBundle:
        """
        Collect all execution artifacts.
        """

        bundle = ArtifactBundle()

        #
        # Screenshot
        #
        try:
            screenshot = self.screenshot_collector.collect(
                run_id=session.session_id,
                page=session.page,
            )
            bundle.screenshots.append(screenshot)
        except Exception:
            pass

        #
        # Trace
        #
        try:
            trace = self.trace_collector.collect(
                run_id=session.session_id,
            )
            bundle.traces.append(trace)
        except Exception:
            pass

        #
        # Video
        #
        try:
            video = self.video_collector.collect(
                session=session,
            )
            bundle.videos.append(video)
        except Exception:
            pass

        #
        # Logs
        #
        bundle.logs = self.log_collector.collect()

        return bundle