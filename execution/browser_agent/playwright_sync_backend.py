"""
======================================================================

Module:
Playwright Sync Backend

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Concrete ``BrowserBackend`` implementation that drives a real
browser via the Playwright Python **synchronous** API.

This class contains all logic that was previously inside
``MCPManager``.  It is the only file in the package that
imports from ``playwright.sync_api``.

Swapping to a different backend (e.g. a future
``PlaywrightMCPBackend``) requires no changes to
``BrowserExecutionAgent`` or any caller — just pass a
different backend instance at construction time.

Architecture
------------
::

    BrowserExecutionAgent
          │  depends on
          ▼
    BrowserBackend (ABC)          ← browser_backend.py
          ▲
          │  implements
    PlaywrightSyncBackend         ← this file

Supported browsers
------------------
chromium (default), firefox, webkit

----------------------------------------------------------------------

TODO:
Support authenticated context (storage state injection).
Support proxy configuration.
Support video recording (context record_video option).
Support multiple concurrent pages.

----------------------------------------------------------------------

INTEGRATION:
Instantiated by BrowserExecutionAgent when no explicit
backend is supplied.
MCPManager delegates to this class (backward-compat shim).

======================================================================
"""

from __future__ import annotations

from typing import Any, Optional

from playwright.sync_api import Playwright, sync_playwright

from execution.browser_agent.browser_backend import (
    BackendSession,
    BrowserBackend,
)
from execution.browser_agent.page_context import PageContext


# Map from public browser_type string to Playwright launcher attribute name.
_BROWSER_ATTR: dict[str, str] = {
    "chromium": "chromium",
    "firefox": "firefox",
    "webkit": "webkit",
}


class PlaywrightSyncBackend(BrowserBackend):
    """
    Drives a real browser through the Playwright Python sync API.

    One ``PlaywrightSyncBackend`` instance manages the
    ``sync_playwright()`` engine.  Each call to
    ``open_session()`` launches a fresh browser + context +
    page, wires a ``PageContext``, navigates to the target URL,
    and returns a ``BackendSession``.  ``close_session()``
    tears down that browser without stopping the engine.

    Parameters
    ----------
    browser_type:
        Browser engine to use: ``"chromium"``, ``"firefox"``,
        or ``"webkit"``.  Defaults to ``"chromium"``.
    headless:
        Run without a visible UI.  Defaults to ``True``.
    slow_mo:
        Slow down every Playwright operation by this many
        milliseconds.  Useful for debugging.  Defaults to 0.
    enable_tracing:
        Automatically start a Playwright trace on each
        browser context.  ``close_session()`` stops the
        trace and returns the ZIP bytes.  Defaults to
        ``True``.
    viewport_width:
        Browser viewport width in pixels.  Defaults to 1280.
    viewport_height:
        Browser viewport height in pixels.  Defaults to 720.
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

        _bt = browser_type.lower()
        if _bt not in _BROWSER_ATTR:
            raise ValueError(
                f"Unsupported browser_type '{browser_type}'. "
                f"Choose from: {sorted(_BROWSER_ATTR.keys())}."
            )

        self._browser_type_str = _bt
        self._headless = headless
        self._slow_mo = slow_mo
        self._enable_tracing = enable_tracing
        self._viewport = {"width": viewport_width, "height": viewport_height}

        # Playwright engine — set by start()
        self._pw: Optional[Playwright] = None

        # Per-session Playwright objects — keyed by run_id so the
        # backend can manage multiple concurrent sessions cleanly.
        # Values: {"browser": …, "context": …, "page": …, "tracing": bool}
        self._sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # BrowserBackend — lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the ``sync_playwright()`` engine.

        Raises
        ------
        RuntimeError
            If already started.
        """
        if self._pw is not None:
            raise RuntimeError(
                "PlaywrightSyncBackend is already started. "
                "Call stop() first."
            )
        self._pw = sync_playwright().start()

    def stop(self) -> None:
        """
        Close any open sessions and stop the Playwright engine.

        Safe to call even if the backend was never started.
        """
        # Close all open sessions first
        for run_id in list(self._sessions.keys()):
            self._close_session_resources(run_id)
        self._sessions.clear()

        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None

    # ------------------------------------------------------------------
    # BrowserBackend — session management
    # ------------------------------------------------------------------

    def open_session(
        self,
        run_id: str,
        url: str,
        navigate_timeout_ms: int = 30_000,
        wait_until: str = "domcontentloaded",
        base_url: Optional[str] = None,
    ) -> BackendSession:
        """
        Launch a browser, create a context + page, wire
        ``PageContext``, navigate to *url*, and return a
        ``BackendSession``.

        Parameters
        ----------
        run_id:
            Unique execution run identifier.
        url:
            Target URL to navigate to.
        navigate_timeout_ms:
            Navigation timeout in milliseconds.
        wait_until:
            Playwright navigation wait strategy.
        base_url:
            Optional base URL for relative navigations.

        Returns
        -------
        BackendSession

        Raises
        ------
        RuntimeError
            If ``start()`` has not been called.
        """
        if self._pw is None:
            raise RuntimeError(
                "PlaywrightSyncBackend has not been started. "
                "Call start() first."
            )

        # ------------------------------------------------------------------
        # 1. Launch browser
        # ------------------------------------------------------------------
        launcher = getattr(self._pw, _BROWSER_ATTR[self._browser_type_str])
        browser: Any = launcher.launch(
            headless=self._headless,
            slow_mo=self._slow_mo,
        )

        # ------------------------------------------------------------------
        # 2. Create context
        # ------------------------------------------------------------------
        context_kwargs: dict[str, Any] = {
            "viewport": self._viewport,
        }
        if base_url:
            context_kwargs["base_url"] = base_url

        context: Any = browser.new_context(**context_kwargs)

        # ------------------------------------------------------------------
        # 3. Start tracing
        # ------------------------------------------------------------------
        tracing_active = False
        if self._enable_tracing:
            context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True,
            )
            tracing_active = True

        # ------------------------------------------------------------------
        # 4. Open page — wire PageContext BEFORE navigation
        # ------------------------------------------------------------------
        page: Any = context.new_page()
        page_ctx = PageContext(run_id=run_id)
        page_ctx.attach(page)

        # ------------------------------------------------------------------
        # 5. Navigate
        # ------------------------------------------------------------------
        page.goto(
            url,
            timeout=navigate_timeout_ms,
            wait_until=wait_until,
        )

        # ------------------------------------------------------------------
        # 6. Store session state for close_session()
        # ------------------------------------------------------------------
        self._sessions[run_id] = {
            "browser": browser,
            "context": context,
            "page": page,
            "page_context": page_ctx,
            "tracing": tracing_active,
        }

        return BackendSession(
            page=page,
            page_context=page_ctx,
            run_id=run_id,
        )

    def close_session(
        self,
        session: BackendSession,
        trace_output_path: str = "trace.zip",
    ) -> Optional[bytes]:
        """
        Stop tracing, close browser resources, and return trace
        bytes.

        The Playwright engine is NOT stopped; it remains
        available for the next ``open_session()`` call.

        Parameters
        ----------
        session:
            The session returned by ``open_session()``.
        trace_output_path:
            Path to write the Playwright trace ZIP.

        Returns
        -------
        bytes | None
            Trace ZIP bytes, or ``None`` when tracing is
            disabled or save failed.
        """
        run_id = session.run_id
        trace_bytes = self._stop_tracing(run_id, trace_output_path)
        self._close_session_resources(run_id)
        return trace_bytes

    # ------------------------------------------------------------------
    # BrowserBackend — identity
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True when the Playwright engine is active."""
        return self._pw is not None

    @property
    def browser_type(self) -> str:
        """Browser engine name (``"chromium"``, ``"firefox"``, ``"webkit"``)."""
        return self._browser_type_str

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _stop_tracing(
        self,
        run_id: str,
        output_path: str,
    ) -> Optional[bytes]:
        """
        Stop the trace for *run_id* and return the ZIP bytes.

        Parameters
        ----------
        run_id:
            Session identifier.
        output_path:
            File path for the trace ZIP.

        Returns
        -------
        bytes | None
        """
        state = self._sessions.get(run_id)
        if state is None or not state.get("tracing"):
            return None

        context: Any = state.get("context")
        if context is None:
            return None

        try:
            context.tracing.stop(path=output_path)
            state["tracing"] = False
            with open(output_path, "rb") as fh:
                return fh.read()
        except Exception:
            return None

    def _close_session_resources(self, run_id: str) -> None:
        """
        Close page, context, and browser for *run_id*.

        Parameters
        ----------
        run_id:
            Session identifier to close.
        """
        state = self._sessions.pop(run_id, None)
        if state is None:
            return

        # Stop tracing if still running (safety net)
        if state.get("tracing") and state.get("context") is not None:
            try:
                state["context"].tracing.stop()
            except Exception:
                pass

        # Clear PageContext
        page_ctx: Any = state.get("page_context")
        if page_ctx is not None:
            try:
                page_ctx.clear()
            except Exception:
                pass

        # Close page
        page: Any = state.get("page")
        if page is not None:
            try:
                page.close()
            except Exception:
                pass

        # Close context
        context: Any = state.get("context")
        if context is not None:
            try:
                context.close()
            except Exception:
                pass

        # Close browser
        browser: Any = state.get("browser")
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
