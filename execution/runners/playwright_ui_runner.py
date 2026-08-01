"""
======================================================================

Module:
Playwright UI Runner

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Executes Playwright UI test functions using the browser
execution infrastructure.

Responsibilities:
- Launch browser sessions
- Execute Playwright UI test functions
- Collect execution artifacts
- Build standardized execution results

This runner intentionally does NOT handle:
- Report generation
- Retry logic
- Self-healing
- AI orchestration

----------------------------------------------------------------------

TODO:
Support dynamically generated Playwright scripts from Engineer 2.

----------------------------------------------------------------------

DUMMY:
Current implementation executes Python callables.

----------------------------------------------------------------------

INTEGRATION:
Engineer 2 will provide dynamically generated Playwright
test functions.

======================================================================
"""

from datetime import datetime
import traceback
from typing import Callable

from execution.browser.playwright_browser_manager import (
    PlaywrightBrowserManager,
)
from execution.collectors.artifact_collector import (
    ArtifactCollector,
)
from execution.enums import ExecutionStatus
from execution.models.execution_request import ExecutionRequest
from execution.models.execution_result import ExecutionResult


class PlaywrightUIRunner:
    """
    Executes Playwright UI test functions using a managed
    browser session.
    """

    def __init__(
        self,
        browser_manager: PlaywrightBrowserManager,
        artifact_collector: ArtifactCollector,
    ) -> None:
        """
        Initialize the UI runner.

        Parameters
        ----------
        browser_manager:
            Browser lifecycle manager.

        artifact_collector:
            Coordinates execution artifact collection.
        """

        self.browser_manager = browser_manager
        self.artifact_collector = artifact_collector

    def execute(
        self,
        request: ExecutionRequest,
        test_function: Callable,
    ) -> ExecutionResult:
        """
        Execute a Playwright UI test function.

        Parameters
        ----------
        request:
            Standardized execution request.

        test_function:
            Callable accepting a Playwright Page object.

        Returns
        -------
        ExecutionResult
        """

        started_at = datetime.utcnow()

        session = self.browser_manager.launch()

        status = ExecutionStatus.PASSED
        error_message = None
        stack_trace = None

        try:

            test_function(session.page)

        except Exception as ex:

            status = ExecutionStatus.FAILED
            error_message = str(ex)
            stack_trace = traceback.format_exc()

        finally:

            artifact_bundle = self.artifact_collector.collect(
                session=session,
            )

            self.browser_manager.close(session)

        completed_at = datetime.utcnow()


        return ExecutionResult(
            run_id=request.run_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
            stack_trace=stack_trace,
        )