"""
======================================================================

Module:
Runner Factory

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Returns the appropriate execution runner based on
ExecutionType.

Design Principles
-----------------
- ExecutionService calls RunnerFactory.create() instead of
  instantiating runners directly.
- RunnerFactory owns all runner instantiation logic so that
  ExecutionService stays free of if/else dispatch chains.
- New runner types (HYBRID, MOBILE, PERFORMANCE) can be
  registered without modifying any caller code.

Supported ExecutionTypes
------------------------
- ExecutionType.UI   → PlaywrightUIRunner
- ExecutionType.API  → PlaywrightAPIRunner
- ExecutionType.HYBRID → Both runners wired in sequence
  (future; raises NotImplementedError until implemented)

----------------------------------------------------------------------

TODO:
Implement HYBRID runner composition.
Support pluggable runner registration.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used exclusively by ExecutionService.

======================================================================
"""

from typing import Callable

from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.collectors.artifact_collector import ArtifactCollector
from execution.collectors.console_log_collector import ConsoleLogCollector
from execution.collectors.log_collector import LogCollector
from execution.collectors.network_collector import NetworkCollector
from execution.collectors.screenshot_collector import ScreenshotCollector
from execution.collectors.trace_collector import TraceCollector
from execution.collectors.video_collector import VideoCollector
from execution.enums import BrowserType, ExecutionType
from execution.models.execution_request import ExecutionRequest
from execution.models.execution_result import ExecutionResult
from execution.runners.playwright_api_runner import PlaywrightAPIRunner
from execution.runners.playwright_ui_runner import PlaywrightUIRunner


class RunnerFactory:
    """
    Creates and configures the appropriate execution runner.

    Usage
    -----
    ::

        runner = RunnerFactory.create(
            engine=engine,
            execution_type=ExecutionType.UI,
        )
        result = runner.execute(request=request, test_function=fn)

    The factory wires all required dependencies (browser
    managers, artifact collectors, optional collectors) so
    callers only have to describe *what* to run, not *how*
    to assemble the runner.
    """

    @staticmethod
    def create(
        engine: PlaywrightEngine,
        execution_type: ExecutionType,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
        enable_console_logs: bool = True,
        enable_network_capture: bool = True,
    ) -> "PlaywrightUIRunner | PlaywrightAPIRunner":
        """
        Construct the correct runner for the given execution type.

        Parameters
        ----------
        engine:
            A *started* PlaywrightEngine instance.  The factory
            does not start/stop the engine; that remains the
            responsibility of ExecutionService.

        execution_type:
            Determines which runner implementation is returned.

        browser_type:
            Browser engine used for UI runs. Ignored for API
            runs.

        headless:
            Run browser headlessly for UI runs. Ignored for
            API runs.

        enable_console_logs:
            When True, attach a ConsoleLogCollector to the
            runner.  Applies to both UI and API runners.

        enable_network_capture:
            When True, attach a NetworkCollector to the runner.
            Applies to both UI and API runners.

        Returns
        -------
        PlaywrightUIRunner | PlaywrightAPIRunner
            Fully configured runner ready for execution.

        Raises
        ------
        NotImplementedError
            If ExecutionType.HYBRID is requested (future).

        ValueError
            If an unknown ExecutionType is supplied.
        """

        if execution_type == ExecutionType.UI:
            return RunnerFactory._create_ui_runner(
                engine=engine,
                browser_type=browser_type,
                headless=headless,
                enable_console_logs=enable_console_logs,
                enable_network_capture=enable_network_capture,
            )

        if execution_type == ExecutionType.API:
            return RunnerFactory._create_api_runner(
                engine=engine,
                enable_console_logs=enable_console_logs,
                enable_network_capture=enable_network_capture,
            )

        if execution_type == ExecutionType.HYBRID:
            raise NotImplementedError(
                "HYBRID execution type is not yet implemented. "
                "It will compose both UI and API runners in "
                "a future release."
            )

        raise ValueError(
            f"Unknown ExecutionType: '{execution_type}'. "
            f"Supported types: UI, API, HYBRID."
        )

    # ------------------------------------------------------------------
    # Private builders
    # ------------------------------------------------------------------

    @staticmethod
    def _create_ui_runner(
        engine: PlaywrightEngine,
        browser_type: BrowserType,
        headless: bool,
        enable_console_logs: bool,
        enable_network_capture: bool,
    ) -> PlaywrightUIRunner:
        """
        Build a fully wired PlaywrightUIRunner.

        Parameters
        ----------
        engine:
            Active PlaywrightEngine.
        browser_type:
            Browser engine.
        headless:
            Headless mode flag.
        enable_console_logs:
            Attach ConsoleLogCollector.
        enable_network_capture:
            Attach NetworkCollector.

        Returns
        -------
        PlaywrightUIRunner
        """

        browser_manager = BrowserFactory.create(
            engine=engine,
            browser_type=browser_type,
            headless=headless,
        )

        console_log_collector = (
            ConsoleLogCollector() if enable_console_logs else None
        )

        network_collector = (
            NetworkCollector() if enable_network_capture else None
        )

        artifact_collector = ArtifactCollector(
            screenshot_collector=ScreenshotCollector(),
            trace_collector=TraceCollector(),
            video_collector=VideoCollector(),
            log_collector=LogCollector(),
            console_log_collector=console_log_collector,
            network_collector=network_collector,
        )

        return PlaywrightUIRunner(
            browser_manager=browser_manager,
            artifact_collector=artifact_collector,
        )

    @staticmethod
    def _create_api_runner(
        engine: PlaywrightEngine,
        enable_console_logs: bool,
        enable_network_capture: bool,
    ) -> PlaywrightAPIRunner:
        """
        Build a fully wired PlaywrightAPIRunner.

        Parameters
        ----------
        engine:
            Active PlaywrightEngine.
        enable_console_logs:
            Attach ConsoleLogCollector.
        enable_network_capture:
            Attach NetworkCollector.

        Returns
        -------
        PlaywrightAPIRunner
        """

        console_log_collector = (
            ConsoleLogCollector() if enable_console_logs else None
        )

        network_collector = (
            NetworkCollector() if enable_network_capture else None
        )

        artifact_collector = ArtifactCollector(
            screenshot_collector=ScreenshotCollector(),
            trace_collector=TraceCollector(),
            video_collector=VideoCollector(),
            log_collector=LogCollector(),
            console_log_collector=console_log_collector,
            network_collector=network_collector,
        )

        return PlaywrightAPIRunner(
            engine=engine,
            artifact_collector=artifact_collector,
            console_log_collector=console_log_collector,
            network_collector=network_collector,
        )
