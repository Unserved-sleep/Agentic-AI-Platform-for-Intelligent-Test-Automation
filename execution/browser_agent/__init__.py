"""
======================================================================

Package:
execution.browser_agent

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Browser automation layer for AI-driven test execution.

Public surface
--------------
Core types (stable public API)::

    BrowserExecutionAgent   — single execution entry-point
    BrowserExecutionResult  — result of one execute() call
    PageContext             — per-page artefact capture
    PageSnapshot            — immutable point-in-time snapshot

Abstraction layer (for backend injection / extension)::

    BrowserBackend          — abstract interface
    BackendSession          — session handle returned by open_session()
    PlaywrightSyncBackend   — concrete Playwright sync implementation

Backward-compatibility shim::

    MCPManager              — legacy wrapper; use PlaywrightSyncBackend
                              for new code

Extension point — future backends
----------------------------------
To add a new backend (e.g. PlaywrightMCPBackend), create a new
file in this package, subclass ``BrowserBackend``, and inject
it::

    from my_package import PlaywrightMCPBackend

    agent = BrowserExecutionAgent(
        backend=PlaywrightMCPBackend(server_url="ws://…")
    )

``BrowserExecutionAgent`` and all callers remain unchanged.

======================================================================
"""

# Core public API
from execution.browser_agent.browser_execution_agent import (
    BrowserExecutionAgent,
    BrowserExecutionResult,
)
from execution.browser_agent.page_context import (
    PageContext,
    PageSnapshot,
)

# Abstraction layer
from execution.browser_agent.browser_backend import (
    BrowserBackend,
    BackendSession,
)
from execution.browser_agent.playwright_sync_backend import (
    PlaywrightSyncBackend,
)

# Backward-compatibility shim
from execution.browser_agent.mcp_manager import MCPManager

__all__ = [
    # Core
    "BrowserExecutionAgent",
    "BrowserExecutionResult",
    "PageContext",
    "PageSnapshot",
    # Abstraction
    "BrowserBackend",
    "BackendSession",
    "PlaywrightSyncBackend",
    # Shim
    "MCPManager",
]
