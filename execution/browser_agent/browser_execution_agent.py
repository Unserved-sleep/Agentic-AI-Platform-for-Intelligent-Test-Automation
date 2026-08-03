"""
======================================================================

Module:
Browser Execution Agent

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Single execution interface for all browser automation.

``BrowserExecutionAgent`` is the public API of the
``execution.browser_agent`` package.  Callers interact
exclusively with this class.  All browser lifecycle and
artefact-capture details are delegated to a pluggable
``BrowserBackend``.

What it does
------------
1. Delegates engine start/stop to the backend.
2. For each ``execute()`` call:
   a. Opens an isolated session via ``backend.open_session()``.
   b. Hands the ``page`` object to the *actions* callable.
   c. Captures the full page state via ``PageContext.capture()``.
   d. Closes the session via ``backend.close_session()`` and
      collects trace bytes.
   e. Returns a ``BrowserExecutionResult``.
3. Guarantees cleanup — session is always closed, even on error.

What it does NOT do
-------------------
- Browser lifecycle details  → backend
- Playwright imports         → backend
- Retry logic                → orchestration/loop.py
- Self-healing               → failure_analysis_agent
- Report generation          → report generators
- AI decisions               → AI agents

Backend injection
-----------------
The constructor accepts an optional ``backend`` argument.
When not supplied, a ``PlaywrightSyncBackend`` is constructed
from the keyword arguments (identical behaviour to before).
To use a different backend::

    agent = BrowserExecutionAgent(
        backend=PlaywrightMCPBackend(server_url="ws://…")
    )

Public API — unchanged from original
--------------------------------------
- ``BrowserExecutionAgent(browser_type, headless, …)``
- ``agent.start()``
- ``agent.execute(url, actions, run_id, …) → BrowserExecutionResult``
- ``agent.stop()``
- ``agent.is_running``
- ``agent.browser_type``
- ``with BrowserExecutionAgent() as agent: …``
- ``BrowserExecutionResult`` dataclass (unchanged fields)

----------------------------------------------------------------------

TODO:
Support inject_cookies / inject_storage before navigation.
Support video recording via backend context options.

----------------------------------------------------------------------

INTEGRATION:
Consumed by orchestration/loop.py (Engineer 2).
Created by RunnerFactory for HYBRID execution type.

======================================================================
"""

from __future__ import annotations

import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from execution.browser_agent.browser_backend import (
    BackendSession,
    BrowserBackend,
)
from execution.browser_agent.inspection_summary import InspectionSummaryBuilder
from execution.browser_agent.page_context import PageContext, PageSnapshot


# ---------------------------------------------------------------------------
# Result model  (public — unchanged)
# ---------------------------------------------------------------------------


@dataclass
class BrowserExecutionResult:
    """
    The result of a single ``BrowserExecutionAgent.execute()`` call.

    Fields
    ------
    run_id:
        Unique execution run identifier.
    passed:
        True when the action callable completed without raising.
    started_at:
        UTC timestamp when execution began.
    completed_at:
        UTC timestamp when execution finished.
    duration_ms:
        Wall-clock duration in milliseconds.
    page_snapshot:
        Full observable page state captured after execution.
        Always present.
    trace_zip:
        Raw Playwright trace ZIP bytes, or None.
    error_message:
        Exception message string, or None when passed.
    stack_trace:
        Full Python traceback, or None when passed.
    metadata:
        Arbitrary key/value data.
    """

    run_id: str
    passed: bool
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    page_snapshot: PageSnapshot
    trace_zip: Optional[bytes] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        """True when the execution did NOT pass."""
        return not self.passed

    @property
    def has_console_errors(self) -> bool:
        """True when the page emitted at least one console ERROR."""
        return self.page_snapshot.has_console_errors

    @property
    def has_network_failures(self) -> bool:
        """True when at least one network request failed."""
        return self.page_snapshot.has_network_failures

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe plain dict."""
        import base64

        trace_b64 = None
        if self.trace_zip is not None:
            trace_b64 = base64.b64encode(self.trace_zip).decode("utf-8")

        return {
            "run_id": self.run_id,
            "passed": self.passed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "trace_zip_b64": trace_b64,
            "page_snapshot": self.page_snapshot.to_dict(),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# BrowserExecutionAgent
# ---------------------------------------------------------------------------


class BrowserExecutionAgent:
    """
    Single execution interface for browser automation.

    ``BrowserExecutionAgent`` depends on ``BrowserBackend``.
    By default it constructs a ``PlaywrightSyncBackend`` from
    the supplied keyword arguments, so existing call-sites that
    pass ``browser_type``, ``headless``, etc. continue to work
    without any changes.

    To swap the implementation, pass a pre-built backend::

        agent = BrowserExecutionAgent(
            backend=PlaywrightSyncBackend(browser_type="firefox")
        )

    Parameters
    ----------
    browser_type:
        Browser engine passed to the default
        ``PlaywrightSyncBackend``.  Ignored when *backend* is
        supplied.  One of ``"chromium"``, ``"firefox"``,
        ``"webkit"``.  Defaults to ``"chromium"``.
    headless:
        Headless flag for the default backend.  Ignored when
        *backend* is supplied.
    slow_mo:
        Slow-motion delay (ms) for the default backend.
        Ignored when *backend* is supplied.
    enable_tracing:
        Trace flag for the default backend.  Ignored when
        *backend* is supplied.
    viewport_width:
        Viewport width for the default backend.  Ignored when
        *backend* is supplied.
    viewport_height:
        Viewport height for the default backend.  Ignored when
        *backend* is supplied.
    trace_output_path:
        File path used when writing the trace ZIP.  Passed to
        ``backend.close_session()``.  Defaults to
        ``"trace.zip"``.
    backend:
        Optional pre-built ``BrowserBackend`` instance.  When
        supplied, all other keyword arguments (browser_type,
        headless, …) are ignored.
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: int = 0,
        enable_tracing: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        trace_output_path: str = "trace.zip",
        backend: Optional[BrowserBackend] = None,
    ) -> None:

        if backend is not None:
            self._backend = backend
        else:
            # Lazy import so the default path still has no import-time
            # dependency on playwright at the module level.
            from execution.browser_agent.playwright_sync_backend import (
                PlaywrightSyncBackend,
            )
            self._backend = PlaywrightSyncBackend(
                browser_type=browser_type,
                headless=headless,
                slow_mo=slow_mo,
                enable_tracing=enable_tracing,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
            )

        self._trace_output_path = trace_output_path

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the browser backend.

        Must be called once before ``execute()``.

        Raises
        ------
        RuntimeError
            If the backend is already running.
        """
        self._backend.start()

    def stop(self) -> None:
        """
        Stop the backend and release all resources.

        Safe to call even if the agent was never fully started.
        """
        self._backend.stop()

    # ------------------------------------------------------------------
    # Main execution entry-point
    # ------------------------------------------------------------------

    def execute(
        self,
        url: str,
        actions: Callable[[Any], None],
        run_id: Optional[str] = None,
        navigate_timeout_ms: int = 30_000,
        wait_until: str = "domcontentloaded",
        metadata: Optional[dict[str, Any]] = None,
    ) -> BrowserExecutionResult:
        """
        Open a browser session, run *actions*, capture all
        artefacts, and return a ``BrowserExecutionResult``.

        The backend must be started via ``start()`` before
        calling this method.

        A fresh isolated session (browser + context + page) is
        opened for each call.  The session is always closed in
        the ``finally`` block, even when *actions* raises.

        Parameters
        ----------
        url:
            URL to navigate to before running actions.
        actions:
            Callable that accepts the live page object and
            performs test actions.
        run_id:
            Execution run identifier.  Auto-generated if None.
        navigate_timeout_ms:
            Navigation timeout in milliseconds.
        wait_until:
            Navigation wait strategy: ``"load"``,
            ``"domcontentloaded"``, ``"networkidle"``,
            ``"commit"``.
        metadata:
            Arbitrary key/value pairs attached to the result.

        Returns
        -------
        BrowserExecutionResult

        Raises
        ------
        RuntimeError
            If ``start()`` has not been called.
        """
        if not self._backend.is_running:
            raise RuntimeError(
                "BrowserExecutionAgent is not started. "
                "Call start() before execute()."
            )

        effective_run_id = run_id or str(uuid.uuid4())
        started_at = datetime.utcnow()

        passed = True
        error_message: Optional[str] = None
        stack_trace_str: Optional[str] = None
        session: Optional[BackendSession] = None
        snapshot: Optional[PageSnapshot] = None
        trace_zip: Optional[bytes] = None

        try:
            # ----------------------------------------------------------------
            # 1. Open session (launch browser, wire PageContext, navigate)
            # ----------------------------------------------------------------
            session = self._backend.open_session(
                run_id=effective_run_id,
                url=url,
                navigate_timeout_ms=navigate_timeout_ms,
                wait_until=wait_until,
            )

            # ----------------------------------------------------------------
            # 2. Execute test actions
            # ----------------------------------------------------------------
            actions(session.page)

        except Exception as exc:
            passed = False
            error_message = str(exc)
            stack_trace_str = traceback.format_exc()

        finally:
            # ----------------------------------------------------------------
            # 3. Capture full page state (always runs, even on failure)
            # ----------------------------------------------------------------
            if session is not None and session.page_context is not None:
                try:
                    snapshot = session.page_context.capture()
                except Exception:
                    snapshot = _empty_snapshot(effective_run_id)
            else:
                snapshot = _empty_snapshot(effective_run_id)

            # ----------------------------------------------------------------
            # 4. Close session — stops tracing, closes browser resources
            # ----------------------------------------------------------------
            if session is not None:
                try:
                    trace_zip = self._backend.close_session(
                        session=session,
                        trace_output_path=self._trace_output_path,
                    )
                except Exception:
                    trace_zip = None

        completed_at = datetime.utcnow()
        duration_ms = (
            completed_at - started_at
        ).total_seconds() * 1000.0

        return BrowserExecutionResult(
            run_id=effective_run_id,
            passed=passed,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            page_snapshot=snapshot,
            trace_zip=trace_zip,
            error_message=error_message,
            stack_trace=stack_trace_str,
            metadata=metadata or {},
        )

    def inspect(
            self,
            url: str,
            run_id: Optional[str] = None,
            navigate_timeout_ms: int = 30_000,
            wait_until: str = "networkidle",
    ) -> PageSnapshot:
        """
        Open a browser session, navigate to the given URL,
        capture the current page state, and return a PageSnapshot.

        Unlike execute(), no browser actions are performed.
        This method is intended for browser inspection and
        prompt enrichment for AI agents.

        Parameters
        ----------
        url:
            URL to inspect.

        run_id:
            Optional inspection identifier. One is generated if omitted.

        navigate_timeout_ms:
            Navigation timeout in milliseconds.

        wait_until:
            Playwright navigation wait strategy.

        Returns
        -------
        PageSnapshot
            Snapshot of the browser state, DOM, screenshot,
            console logs and network events.

        Raises
        ------
        RuntimeError
            If inspection fails.
        """

        owns_backend = False
        session: Optional[BackendSession] = None

        effective_run_id = run_id or f"inspection-{uuid.uuid4()}"

        try:
            # Start backend only if not already running
            if not self._backend.is_running:
                self.start()
                owns_backend = True

            # Open isolated browser session
            session = self._backend.open_session(
                run_id=effective_run_id,
                url=url,
                navigate_timeout_ms=navigate_timeout_ms,
                wait_until=wait_until,
            )

            # Capture page state
            snapshot = session.page_context.capture()

            return snapshot

        finally:
            # Always close browser session
            if session is not None:
                try:
                    self._backend.close_session(
                        session=session,
                        trace_output_path=self._trace_output_path,
                    )
                except Exception:
                    pass

            # Stop backend only if we started it
            if owns_backend:
                try:
                    self.stop()
                except Exception:
                    pass

    def inspect_summary(
            self,
            url: str,
    ):
        snapshot = self.inspect(url)
        return InspectionSummaryBuilder.from_snapshot(snapshot)

    # ------------------------------------------------------------------
    # Context-manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "BrowserExecutionAgent":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True when the backend is active."""
        return self._backend.is_running

    @property
    def browser_type(self) -> str:
        """The configured browser engine name."""
        return self._backend.browser_type


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------


def _empty_snapshot(run_id: str) -> PageSnapshot:
    """
    Return a minimal valid PageSnapshot for failure paths.

    Ensures ``BrowserExecutionResult.page_snapshot`` is never
    None even when capture itself raises.
    """
    from execution.collectors.network_collector import NetworkEventBundle
    from execution.models.browser_state import BrowserState
    from execution.models.dom_snapshot import DOMSnapshot

    return PageSnapshot(
        run_id=run_id,
        captured_at=datetime.utcnow(),
        browser_state=BrowserState(current_url=""),
        dom_snapshot=DOMSnapshot(url="", html=""),
        screenshot_png=None,
        console_logs=[],
        network_events=NetworkEventBundle(),
    )
