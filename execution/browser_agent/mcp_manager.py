"""
======================================================================

Module:
MCP Manager  (backward-compatibility shim)

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Thin shim that preserves the original MCPManager public API
while delegating all real work to ``PlaywrightSyncBackend``.

Why this file still exists
---------------------------
Before the ``BrowserBackend`` abstraction was introduced,
``BrowserExecutionAgent`` owned an ``MCPManager`` directly.
Any external code that imported ``MCPManager`` and used its
methods (``start``, ``stop``, ``launch_browser``, ``new_page``,
``stop_tracing``, ``page``, ``context``, ``browser``,
``is_running``, ``is_browser_open``, ``browser_type``,
``page_context``) would break if the class disappeared.

This shim re-exposes exactly that surface.  No new code
should use it; prefer ``PlaywrightSyncBackend`` directly or
inject a backend into ``BrowserExecutionAgent``.

----------------------------------------------------------------------

TODO:
Remove once all callers have migrated to BrowserBackend / 
PlaywrightSyncBackend.

----------------------------------------------------------------------

INTEGRATION:
Imported by legacy code and tests only.
BrowserExecutionAgent no longer uses this class.

======================================================================
"""

from __future__ import annotations

from typing import Any, Optional

from execution.browser_agent.page_context import PageContext
from execution.browser_agent.playwright_sync_backend import (
    PlaywrightSyncBackend,
)


class MCPManager:
    """
    Backward-compatibility shim.

    Wraps ``PlaywrightSyncBackend`` and re-exposes the original
    MCPManager API.  New code should use
    ``PlaywrightSyncBackend`` or inject a ``BrowserBackend``
    into ``BrowserExecutionAgent`` instead.

    Parameters
    ----------
    browser_type:
        See ``PlaywrightSyncBackend``.
    headless:
        See ``PlaywrightSyncBackend``.
    slow_mo:
        See ``PlaywrightSyncBackend``.
    enable_tracing:
        See ``PlaywrightSyncBackend``.
    viewport_width:
        See ``PlaywrightSyncBackend``.
    viewport_height:
        See ``PlaywrightSyncBackend``.
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: int = 0,
        enable_tracing: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> None:

        self._backend = PlaywrightSyncBackend(
            browser_type=browser_type,
            headless=headless,
            slow_mo=slow_mo,
            enable_tracing=enable_tracing,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )

        # The current open session run_id — set by new_page()
        self._current_run_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Engine lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the Playwright engine."""
        self._backend.start()

    def stop(self) -> None:
        """Stop the Playwright engine and all sessions."""
        self._backend.stop()
        self._current_run_id = None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def launch_browser(
        self,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Launch a browser and open a page.

        Stores session state internally so that ``page``,
        ``context``, ``browser``, and ``page_context``
        properties work.

        .. note::
            ``new_page()`` must be called after this to attach
            a ``PageContext``.  This matches the original API
            where ``launch_browser()`` + ``new_page()`` were
            two separate steps.

        Parameters
        ----------
        base_url:
            Optional base URL for relative navigations.
        """
        # We need a temporary run_id so the backend can store state.
        # It will be replaced when new_page() is called.
        import uuid
        temp_run_id = str(uuid.uuid4())
        self._current_run_id = temp_run_id

        # Open a session but navigate to about:blank so the caller
        # can navigate later via manager.page.goto(…)
        from execution.browser_agent.browser_backend import BackendSession
        backend = self._backend

        # Manually launch browser without navigating (replicate original
        # MCPManager.launch_browser which opened resources without nav)
        from playwright.sync_api import sync_playwright  # only used here

        if backend._pw is None:
            raise RuntimeError(
                "Playwright engine is not running. Call start() first."
            )

        from execution.browser_agent.playwright_sync_backend import (
            _BROWSER_ATTR,
        )

        launcher = getattr(backend._pw, _BROWSER_ATTR[backend._browser_type_str])
        browser: Any = launcher.launch(
            headless=backend._headless,
            slow_mo=backend._slow_mo,
        )

        context_kwargs: dict[str, Any] = {
            "viewport": backend._viewport,
        }
        if base_url:
            context_kwargs["base_url"] = base_url

        context: Any = browser.new_context(**context_kwargs)

        tracing_active = False
        if backend._enable_tracing:
            context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True,
            )
            tracing_active = True

        page: Any = context.new_page()

        # Store in backend's session table under temp_run_id
        backend._sessions[temp_run_id] = {
            "browser": browser,
            "context": context,
            "page": page,
            "page_context": None,    # set by new_page()
            "tracing": tracing_active,
        }

    def new_page(self, run_id: str) -> PageContext:
        """
        Attach a ``PageContext`` to the current page.

        Must be called after ``launch_browser()``.

        Parameters
        ----------
        run_id:
            Execution run identifier.

        Returns
        -------
        PageContext
        """
        if self._current_run_id is None:
            raise RuntimeError(
                "Browser has not been launched. "
                "Call launch_browser() first."
            )

        backend = self._backend
        state = backend._sessions.get(self._current_run_id)
        if state is None or state.get("page") is None:
            raise RuntimeError(
                "Browser page is not available. "
                "Call launch_browser() first."
            )

        # Re-key the session under the real run_id if it differs
        if run_id != self._current_run_id:
            backend._sessions[run_id] = backend._sessions.pop(
                self._current_run_id
            )
            self._current_run_id = run_id

        page_ctx = PageContext(run_id=run_id)
        page_ctx.attach(state["page"])
        state["page_context"] = page_ctx

        return page_ctx

    def stop_tracing(
        self,
        output_path: str = "trace.zip",
    ) -> Optional[bytes]:
        """
        Stop tracing and return the ZIP bytes.

        Parameters
        ----------
        output_path:
            File path for the trace ZIP.

        Returns
        -------
        bytes | None
        """
        if self._current_run_id is None:
            return None
        return self._backend._stop_tracing(
            self._current_run_id,
            output_path,
        )

    # ------------------------------------------------------------------
    # Accessors — mirroring the original MCPManager property surface
    # ------------------------------------------------------------------

    @property
    def page(self) -> Any:
        """Active Playwright Page."""
        state = self._current_state()
        pg = state.get("page")
        if pg is None:
            raise RuntimeError(
                "No active page. Call launch_browser() first."
            )
        return pg

    @property
    def context(self) -> Any:
        """Active Playwright BrowserContext."""
        state = self._current_state()
        ctx = state.get("context")
        if ctx is None:
            raise RuntimeError(
                "No active context. Call launch_browser() first."
            )
        return ctx

    @property
    def browser(self) -> Any:
        """Active Playwright Browser."""
        state = self._current_state()
        br = state.get("browser")
        if br is None:
            raise RuntimeError(
                "No active browser. Call launch_browser() first."
            )
        return br

    @property
    def page_context(self) -> Optional[PageContext]:
        """The PageContext for the current page, or None."""
        if self._current_run_id is None:
            return None
        state = self._backend._sessions.get(self._current_run_id, {})
        return state.get("page_context")

    @property
    def is_running(self) -> bool:
        """True when the Playwright engine is active."""
        return self._backend.is_running

    @property
    def is_browser_open(self) -> bool:
        """True when a browser session is currently open."""
        if self._current_run_id is None:
            return False
        state = self._backend._sessions.get(self._current_run_id, {})
        return state.get("browser") is not None

    @property
    def browser_type(self) -> str:
        """The browser engine name."""
        return self._backend.browser_type

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _current_state(self) -> dict[str, Any]:
        if self._current_run_id is None:
            return {}
        return self._backend._sessions.get(self._current_run_id, {})
