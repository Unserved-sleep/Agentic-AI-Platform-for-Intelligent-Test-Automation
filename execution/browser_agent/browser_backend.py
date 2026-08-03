"""
======================================================================

Module:
Browser Backend (Abstract Interface)

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the abstract contract that any browser backend must
satisfy to be usable by ``BrowserExecutionAgent``.

Rationale
---------
``BrowserExecutionAgent`` is the single execution interface
consumed by the rest of the platform.  It must remain stable
regardless of *how* the browser is driven.  Today that is
the Playwright Python sync API (``PlaywrightSyncBackend``).
In future it could be the Playwright MCP server/client
protocol (``PlaywrightMCPBackend``) or another tool entirely.

This interface is the seam.  ``BrowserExecutionAgent`` depends
only on ``BrowserBackend``.  The concrete implementation is
injected at construction time and can be swapped without
touching the agent or any caller.

Contract summary
----------------
A ``BrowserBackend`` is responsible for exactly three things:

1. **Lifecycle** — ``start()`` / ``stop()``
   Boot and tear down whatever underlying resource the
   backend requires (a Playwright engine, an MCP subprocess,
   a remote WebDriver session, etc.).

2. **Session management** — ``open_session()`` / ``close_session()``
   Open an isolated browser session for one test run:
   navigate to a URL, attach event listeners via
   ``PageContext``, and return a ``BackendSession`` that
   ``BrowserExecutionAgent`` can drive with a ``page``
   object (``Any``).  After the test, close the session
   and return any trace bytes.

3. **Identity** — ``is_running``, ``browser_type``
   Expose just enough state for the agent to guard against
   misuse and for logging.

Extension point — future PlaywrightMCPBackend
---------------------------------------------
When a Playwright MCP backend is added, create a new file::

    execution/browser_agent/playwright_mcp_backend.py

Subclass ``BrowserBackend`` and implement the four abstract
methods.  ``BrowserExecutionAgent`` does not need to change;
callers construct the agent with::

    agent = BrowserExecutionAgent(
        backend=PlaywrightMCPBackend(server_url="ws://…")
    )

======================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


# ---------------------------------------------------------------------------
# BackendSession — the handle returned by open_session()
# ---------------------------------------------------------------------------


@dataclass
class BackendSession:
    """
    Represents one open browser session managed by a backend.

    A session is a single isolated execution context: one
    browser, one context, one page.  ``BrowserExecutionAgent``
    uses the ``page`` object to drive test actions and the
    ``page_context`` object to capture browser state.

    Fields
    ------
    page:
        The live browser page object.  For
        ``PlaywrightSyncBackend`` this is a
        ``playwright.sync_api.Page``.  For a future MCP backend
        this would be a proxy/stub with the same interface.
        Typed as ``Any`` to stay backend-agnostic.
    page_context:
        The ``PageContext`` wired to *page*.  Already has
        console- and network-event listeners attached.
    run_id:
        The execution run identifier passed to
        ``open_session()``.
    """

    page: Any
    page_context: Any          # PageContext — typed Any to avoid circular import
    run_id: str


# ---------------------------------------------------------------------------
# BrowserBackend — abstract base class
# ---------------------------------------------------------------------------


class BrowserBackend(ABC):
    """
    Abstract contract for a browser backend.

    Subclass this to introduce a new browser execution
    strategy.  The four abstract methods are the only
    integration points ``BrowserExecutionAgent`` calls.

    Implementations must be safe to use as a context manager
    via the default ``__enter__`` / ``__exit__`` provided here,
    which simply call ``start()`` and ``stop()``.
    """

    # ------------------------------------------------------------------
    # Lifecycle (must implement)
    # ------------------------------------------------------------------

    @abstractmethod
    def start(self) -> None:
        """
        Start the backend.

        For ``PlaywrightSyncBackend`` this starts the
        ``sync_playwright()`` context.  For a future MCP
        backend this would launch or connect to the MCP
        server process.

        Must be called once before ``open_session()``.

        Raises
        ------
        RuntimeError
            If the backend is already running.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the backend and release all resources.

        Must clean up everything opened by ``start()``.
        Safe to call even if ``start()`` was never called.
        """

    # ------------------------------------------------------------------
    # Session management (must implement)
    # ------------------------------------------------------------------

    @abstractmethod
    def open_session(
        self,
        run_id: str,
        url: str,
        navigate_timeout_ms: int = 30_000,
        wait_until: str = "domcontentloaded",
        base_url: Optional[str] = None,
    ) -> BackendSession:
        """
        Open an isolated browser session and navigate to *url*.

        This method must:
        1. Launch a browser + context + page.
        2. Create a ``PageContext`` and call ``attach(page)``
           *before* navigating, so no events are missed.
        3. Navigate to *url*.
        4. Return a ``BackendSession``.

        Parameters
        ----------
        run_id:
            Unique execution run identifier.  Attached to all
            captured artefacts.
        url:
            The URL to navigate to.
        navigate_timeout_ms:
            Navigation timeout in milliseconds.
        wait_until:
            Playwright-style navigation wait strategy:
            ``"load"``, ``"domcontentloaded"``,
            ``"networkidle"``, or ``"commit"``.
        base_url:
            Optional base URL for relative navigations.

        Returns
        -------
        BackendSession
            Open session with ``page`` and ``page_context``
            ready for use.

        Raises
        ------
        RuntimeError
            If the backend has not been started.
        """

    @abstractmethod
    def close_session(
        self,
        session: BackendSession,
        trace_output_path: str = "trace.zip",
    ) -> Optional[bytes]:
        """
        Close *session* and return any trace bytes.

        This method must:
        1. Stop any trace recording.
        2. Close the page, context, and browser.
        3. Return the raw trace ZIP bytes, or ``None`` when
           tracing is disabled or unavailable.

        The backend engine itself (started by ``start()``)
        must NOT be stopped here.  Only per-session resources
        are released, allowing the same backend to be reused
        across multiple sessions.

        Parameters
        ----------
        session:
            The session returned by ``open_session()``.
        trace_output_path:
            File path to write the Playwright trace ZIP.

        Returns
        -------
        bytes | None
            Trace ZIP bytes, or None.
        """

    # ------------------------------------------------------------------
    # Identity (must implement)
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        Return True when the backend has been started and not
        yet stopped.
        """

    @property
    @abstractmethod
    def browser_type(self) -> str:
        """
        Human-readable name of the browser engine being driven,
        e.g. ``"chromium"``, ``"firefox"``, ``"webkit"``, or
        ``"mcp"`` for a future MCP backend.
        """

    # ------------------------------------------------------------------
    # Context-manager support (provided; do not override)
    # ------------------------------------------------------------------

    def __enter__(self) -> "BrowserBackend":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        self.stop()
