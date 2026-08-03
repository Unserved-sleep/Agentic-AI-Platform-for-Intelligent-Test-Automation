"""
======================================================================

Module:
Page Context

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Captures the complete observable state of a live Playwright
page at any point during execution.

PageContext is the MCP layer's data-collection hub.  It holds
references to the five collectors and exposes a single
``capture()`` method that snapshots everything in one call.

What it captures
----------------
1. BrowserState   — URL, title, cookies, localStorage,
                    sessionStorage, viewport, user-agent
2. DOMSnapshot    — Full page HTML + plain-text content
3. Screenshot     — PNG bytes of the current viewport
4. ConsoleLog     — All browser console messages collected
                    since ``attach()`` was called
5. NetworkEvents  — All HTTP requests / responses / failures
                    collected since ``attach()`` was called

Each capture returns a ``PageSnapshot`` — a frozen dataclass
that bundles all five artefacts with a run_id and timestamp.
No Playwright objects are kept after capture.

Usage
-----
::

    ctx = PageContext(run_id="run-001")
    ctx.attach(page)          # wire event listeners

    # … run test actions on page …

    snapshot = ctx.capture()  # PageSnapshot

    ctx.clear()               # reset for next page

----------------------------------------------------------------------

TODO:
Support partial DOM capture (scoped to a CSS selector).
Support accessibility tree snapshot.
Support capturing open network connections / pending requests.

----------------------------------------------------------------------

INTEGRATION:
Created and owned by MCPManager.
Consumed by BrowserExecutionAgent.

======================================================================
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from execution.collectors.console_log_collector import (
    ConsoleLogCollector,
    ConsoleLogEntry,
)
from execution.collectors.network_collector import (
    NetworkCollector,
    NetworkEventBundle,
)
from execution.models.browser_state import BrowserState, ViewportSize
from execution.models.dom_snapshot import DOMSnapshot


# ---------------------------------------------------------------------------
# PageSnapshot — immutable result produced by PageContext.capture()
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PageSnapshot:
    """
    Immutable point-in-time snapshot of a page's full observable
    state.

    Produced by ``PageContext.capture()`` and consumed by
    ``BrowserExecutionAgent`` when assembling the final
    ``BrowserExecutionResult``.

    Fields
    ------
    run_id:
        Execution run identifier.
    captured_at:
        UTC timestamp when ``capture()`` was called.
    browser_state:
        URL, title, cookies, storage, viewport.
    dom_snapshot:
        Full page HTML + plain-text content.
    screenshot_png:
        Raw PNG bytes of the viewport.  ``None`` when
        screenshot capture failed or was skipped.
    console_logs:
        All browser console messages captured since
        ``PageContext.attach()`` was called.
    network_events:
        All HTTP network events captured since
        ``PageContext.attach()`` was called.
    """

    run_id: str
    captured_at: datetime
    browser_state: BrowserState
    dom_snapshot: DOMSnapshot
    screenshot_png: Optional[bytes]
    console_logs: list[ConsoleLogEntry]
    network_events: NetworkEventBundle

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def screenshot_b64(self) -> Optional[str]:
        """
        Return screenshot as a Base64-encoded string, or None.

        Useful for embedding in JSON payloads sent to AI agents.
        """
        if self.screenshot_png is None:
            return None
        return base64.b64encode(self.screenshot_png).decode("utf-8")

    @property
    def has_console_errors(self) -> bool:
        """Return True if any ERROR-level console message was captured."""
        return any(e.level == "ERROR" for e in self.console_logs)

    @property
    def has_network_failures(self) -> bool:
        """Return True if any network request failed."""
        return self.network_events.has_failures()

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise the snapshot to a plain dict (JSON-safe).

        Screenshot bytes are Base64-encoded.  Pydantic models
        are converted via ``model_dump()``.

        Returns
        -------
        dict
        """
        return {
            "run_id": self.run_id,
            "captured_at": self.captured_at.isoformat(),
            "browser_state": self.browser_state.model_dump(mode="json"),
            "dom_snapshot": self.dom_snapshot.model_dump(mode="json"),
            "screenshot_b64": self.screenshot_b64,
            "console_logs": [
                e.model_dump(mode="json") for e in self.console_logs
            ],
            "network_events": self.network_events.model_dump(mode="json"),
        }


# ---------------------------------------------------------------------------
# PageContext
# ---------------------------------------------------------------------------


class PageContext:
    """
    Captures the full observable state of a live Playwright page.

    PageContext wires five collectors to a Playwright Page object
    and exposes ``capture()`` to take a complete snapshot at any
    point during execution.

    Typical lifecycle
    -----------------
    1. Create: ``ctx = PageContext(run_id="…")``
    2. Attach: ``ctx.attach(page)``  — registers event listeners
    3. Run test actions on the page
    4. Snapshot: ``snapshot = ctx.capture()``
    5. Reset:   ``ctx.clear()``  — optional, enables reuse

    Parameters
    ----------
    run_id:
        Execution run identifier attached to all captured
        artefacts.
    """

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._page: Any = None

        # Collectors
        self._console_collector = ConsoleLogCollector()
        self._network_collector = NetworkCollector()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def attach(self, page: Any) -> None:
        """
        Wire all event listeners to *page*.

        Must be called before test actions start so that
        console and network events are not missed.

        Parameters
        ----------
        page:
            An active ``playwright.sync_api.Page`` instance.
        """
        self._page = page
        self._console_collector.attach(page)
        self._network_collector.attach(page)

    def clear(self) -> None:
        """
        Clear all buffered events and release the page reference.

        Call this between tests when reusing the same
        ``PageContext`` instance.
        """
        self._console_collector.clear()
        self._network_collector.clear()
        self._page = None

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def capture(self) -> PageSnapshot:
        """
        Capture the full observable state of the page right now.

        Captures (in order):
        1. BrowserState  — URL, title, cookies, storage, viewport
        2. DOMSnapshot   — Full HTML + text content
        3. Screenshot    — PNG bytes
        4. ConsoleLog    — All buffered console entries
        5. NetworkEvents — All buffered network events

        Each item is captured independently.  A failure in one
        capture (e.g. page navigated away) does not prevent the
        others from running.

        Returns
        -------
        PageSnapshot
            Immutable snapshot of all captured state.

        Raises
        ------
        RuntimeError
            If ``attach()`` has not been called before ``capture()``.
        """
        if self._page is None:
            raise RuntimeError(
                "PageContext.attach(page) must be called before capture()."
            )

        captured_at = datetime.utcnow()

        browser_state = self._capture_browser_state()
        dom_snapshot = self._capture_dom_snapshot()
        screenshot_png = self._capture_screenshot()
        console_logs = self._console_collector.collect()
        network_events = self._network_collector.collect()

        return PageSnapshot(
            run_id=self._run_id,
            captured_at=captured_at,
            browser_state=browser_state,
            dom_snapshot=dom_snapshot,
            screenshot_png=screenshot_png,
            console_logs=console_logs,
            network_events=network_events,
        )

    # ------------------------------------------------------------------
    # Private capture helpers
    # ------------------------------------------------------------------

    def _capture_browser_state(self) -> BrowserState:
        """
        Build a BrowserState from the live page.

        Each attribute is fetched independently so a failure
        (e.g. page unloading during capture) produces a
        partial but valid BrowserState rather than an exception.

        Returns
        -------
        BrowserState
        """
        url = ""
        title = ""
        cookies: list[dict[str, Any]] = []
        viewport: Optional[ViewportSize] = None
        local_storage: dict[str, str] = {}
        session_storage: dict[str, str] = {}
        user_agent = ""

        # URL
        try:
            url = self._page.url or ""
        except Exception:
            pass

        # Title
        try:
            title = self._page.title() or ""
        except Exception:
            pass

        # Cookies — from the browser context
        try:
            raw_cookies = self._page.context.cookies()
            if isinstance(raw_cookies, list):
                cookies = raw_cookies
        except Exception:
            pass

        # Viewport
        try:
            vp = self._page.viewport_size
            if vp and isinstance(vp, dict):
                viewport = ViewportSize(
                    width=vp.get("width", 1280),
                    height=vp.get("height", 720),
                )
        except Exception:
            pass

        # localStorage
        try:
            raw_ls: Any = self._page.evaluate(
                "() => { "
                "  const s = {}; "
                "  for (let i = 0; i < localStorage.length; i++) { "
                "    const k = localStorage.key(i); "
                "    s[k] = localStorage.getItem(k); "
                "  } "
                "  return s; "
                "}"
            )
            if isinstance(raw_ls, dict):
                local_storage = {
                    str(k): str(v) for k, v in raw_ls.items()
                }
        except Exception:
            pass

        # sessionStorage
        try:
            raw_ss: Any = self._page.evaluate(
                "() => { "
                "  const s = {}; "
                "  for (let i = 0; i < sessionStorage.length; i++) { "
                "    const k = sessionStorage.key(i); "
                "    s[k] = sessionStorage.getItem(k); "
                "  } "
                "  return s; "
                "}"
            )
            if isinstance(raw_ss, dict):
                session_storage = {
                    str(k): str(v) for k, v in raw_ss.items()
                }
        except Exception:
            pass

        # User-Agent
        try:
            user_agent = self._page.evaluate(
                "() => navigator.userAgent"
            ) or ""
        except Exception:
            pass

        return BrowserState(
            current_url=url,
            title=title,
            cookies=cookies,
            viewport=viewport,
            local_storage=local_storage,
            session_storage=session_storage,
            user_agent=user_agent,
        )

    def _capture_dom_snapshot(self) -> DOMSnapshot:
        """
        Capture the full HTML and text content of the page.

        Returns
        -------
        DOMSnapshot
        """
        url = ""
        html = ""
        text_content = ""

        try:
            url = self._page.url or ""
        except Exception:
            pass

        # Full outer HTML
        try:
            html = self._page.evaluate(
                "() => document.documentElement.outerHTML"
            ) or ""
        except Exception:
            pass

        # Plain-text content
        try:
            text_content = self._page.evaluate(
                "() => document.body ? document.body.innerText : ''"
            ) or ""
        except Exception:
            pass

        return DOMSnapshot(
            url=url,
            html=html,
            text_content=text_content,
            run_id=self._run_id,
        )

    def _capture_screenshot(self) -> Optional[bytes]:
        """
        Take a full-page PNG screenshot.

        Returns
        -------
        bytes | None
            PNG bytes on success, None on failure.
        """
        try:
            return self._page.screenshot(full_page=True)
        except Exception:
            # Attempt a viewport-only screenshot as a fallback
            try:
                return self._page.screenshot()
            except Exception:
                return None

    # ------------------------------------------------------------------
    # Accessor properties
    # ------------------------------------------------------------------

    @property
    def run_id(self) -> str:
        """The execution run identifier this context belongs to."""
        return self._run_id

    @property
    def console_collector(self) -> ConsoleLogCollector:
        """The underlying ConsoleLogCollector instance."""
        return self._console_collector

    @property
    def network_collector(self) -> NetworkCollector:
        """The underlying NetworkCollector instance."""
        return self._network_collector
