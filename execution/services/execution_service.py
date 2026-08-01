"""
======================================================================

Module:
Execution Service

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Provides the public API for executing Playwright UI tests.

ExecutionService is responsible for:
- Managing the Playwright engine lifecycle
- Creating browser managers
- Wiring execution dependencies
- Executing UI tests
- Returning standardized execution results

----------------------------------------------------------------------

TODO:
Support API, Mobile and Performance execution types.

----------------------------------------------------------------------

INTEGRATION:
Primary entry point used by Engineer 2.

======================================================================
"""

from typing import Callable

from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.collectors.artifact_collector import ArtifactCollector
from execution.collectors.log_collector import LogCollector
from execution.collectors.screenshot_collector import ScreenshotCollector
from execution.collectors.trace_collector import TraceCollector
from execution.collectors.video_collector import VideoCollector
from execution.enums import BrowserType
from execution.models.execution_request import ExecutionRequest
from execution.models.execution_result import ExecutionResult
from execution.runners.playwright_ui_runner import PlaywrightUIRunner


class ExecutionService:
    """
    Public execution entry point.
    """

    def __init__(self) -> None:

        self.engine = PlaywrightEngine()

    def execute(
        self,
        request: ExecutionRequest,
        test_function: Callable,
    ) -> ExecutionResult:
        """
        Execute a Playwright UI test.
        """

        self.engine.start()

        try:

            browser_manager = BrowserFactory.create(
                engine=self.engine,
                browser_type=BrowserType.CHROMIUM,
            )

            screenshot_collector = ScreenshotCollector()
            trace_collector = TraceCollector()
            video_collector = VideoCollector()
            log_collector = LogCollector()

            artifact_collector = ArtifactCollector(
                screenshot_collector=screenshot_collector,
                trace_collector=trace_collector,
                video_collector=video_collector,
                log_collector=log_collector,
            )

            runner = PlaywrightUIRunner(
                browser_manager=browser_manager,
                artifact_collector=artifact_collector,
            )

            return runner.execute(
                request=request,
                test_function=test_function,
            )

        finally:

            self.engine.stop()