"""
======================================================================

Module:
Playwright API Runner

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Executes Playwright API test callables using
APIRequestContext.

Responsibilities:
- Start Playwright engine
- Create APIRequestContext
- Execute API test functions
- Collect execution artifacts (logs, console output)
- Build standardized ExecutionResult with ArtifactBundle
- Handle failures with full traceback
- Record execution timing (started_at, completed_at, duration_ms)

This runner intentionally does NOT handle:
- Report generation
- Retry logic
- Self-healing
- AI orchestration

----------------------------------------------------------------------

TODO:
Support base URL injection from ExecutionRequest metadata.

----------------------------------------------------------------------

DUMMY:
Current implementation executes Python callables that
accept an APIRequestContext argument.

----------------------------------------------------------------------

INTEGRATION:
Engineer 2 will provide dynamically generated API test
callables that expect an APIRequestContext.

Engineer 3's RunnerFactory returns this runner when
ExecutionType is API.

======================================================================
"""

from datetime import datetime
import traceback
from typing import Callable

from execution.browser.playwright_engine import PlaywrightEngine
from execution.collectors.artifact_collector import ArtifactCollector
from execution.collectors.console_log_collector import ConsoleLogCollector
from execution.collectors.network_collector import NetworkCollector
from execution.enums import ExecutionStatus
from execution.models.execution_request import ExecutionRequest
from execution.models.execution_result import ExecutionResult
from execution.models.artifact_bundle import ArtifactBundle


class PlaywrightAPIRunner:
    """
    Executes Playwright API test callables using
    APIRequestContext.

    This runner does not launch a browser. It creates an
    isolated APIRequestContext suitable for HTTP-level
    testing (REST/GraphQL/JSON contract tests).

    Enhancements over the initial stub:
    - Writes collected console logs as an Artifact into the bundle
    - Records full execution timing (duration_ms)
    - Integrates optional ConsoleLogCollector and NetworkCollector
    """

    def __init__(
        self,
        engine: PlaywrightEngine,
        artifact_collector: ArtifactCollector,
        console_log_collector: ConsoleLogCollector | None = None,
        network_collector: NetworkCollector | None = None,
    ) -> None:
        """
        Initialize the API runner.

        Parameters
        ----------
        engine:
            A started PlaywrightEngine instance.

        artifact_collector:
            Coordinates execution artifact collection.

        console_log_collector:
            Optional collector for console-level messages
            produced during test execution.

        network_collector:
            Optional collector for HTTP request/response
            events produced during test execution.
        """

        self.engine = engine
        self.artifact_collector = artifact_collector
        self.console_log_collector = console_log_collector
        self.network_collector = network_collector

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        request: ExecutionRequest,
        test_function: Callable,
    ) -> ExecutionResult:
        """
        Execute a Playwright API test callable.

        The test_function must accept a single positional
        argument: playwright.sync_api.APIRequestContext.

        Execution flow
        --------------
        1. Record start time.
        2. Create an APIRequestContext (base_url from metadata).
        3. Invoke the test callable.
        4. On failure: capture error_message + stack_trace.
        5. Always dispose the APIRequestContext.
        6. Collect artifacts (console logs, network events).
        7. Build and return ExecutionResult.

        Parameters
        ----------
        request:
            Standardized execution request.

        test_function:
            Callable accepting a Playwright APIRequestContext.

        Returns
        -------
        ExecutionResult
        """

        started_at = datetime.utcnow()

        status = ExecutionStatus.PASSED
        error_message = None
        stack_trace = None

        api_context = self._create_api_context(request)

        try:
            test_function(api_context)

        except Exception as ex:
            status = ExecutionStatus.FAILED
            error_message = str(ex)
            stack_trace = traceback.format_exc()

        finally:
            self._dispose_api_context(api_context)

        completed_at = datetime.utcnow()

        # Build artifact bundle from available collectors.
        artifact_bundle = self._collect_artifacts(
            run_id=request.run_id,
        )

        return ExecutionResult(
            run_id=request.run_id,
            status=status,
            artifacts=artifact_bundle,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
            stack_trace=stack_trace,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_api_context(
        self,
        request: ExecutionRequest,
    ):
        """
        Create a Playwright APIRequestContext.

        The base URL is injected via request.metadata under
        the key "base_url". If absent, no base URL is
        configured.

        Parameters
        ----------
        request:
            Execution request, inspected for base_url
            in metadata.

        Returns
        -------
        playwright.sync_api.APIRequestContext
        """

        base_url: str | None = request.metadata.get("base_url")

        kwargs: dict = {}

        if base_url:
            kwargs["base_url"] = base_url

        return self.engine.playwright.request.new_context(**kwargs)

    @staticmethod
    def _dispose_api_context(api_context) -> None:
        """
        Dispose the APIRequestContext to release connections.

        Parameters
        ----------
        api_context:
            The Playwright APIRequestContext to dispose.
        """

        try:
            api_context.dispose()
        except Exception:
            pass

    def _collect_artifacts(
        self,
        run_id: str,
    ) -> ArtifactBundle:
        """
        Build an ArtifactBundle from available collectors.

        For API tests there is no browser page, so screenshots,
        traces, and videos are not applicable. Only console
        logs and network events are collected if their
        respective collectors are configured.

        Parameters
        ----------
        run_id:
            Unique execution identifier used for artifact
            directory naming.

        Returns
        -------
        ArtifactBundle
        """

        # Start with an empty bundle.
        bundle = ArtifactBundle()

        # Collect console logs if a collector was provided.
        if self.console_log_collector is not None:
            bundle.console_logs = (
                self.console_log_collector.collect()
            )

        # Collect network events if a collector was provided.
        if self.network_collector is not None:
            bundle.network_events = (
                self.network_collector.collect()
            )

        return bundle
