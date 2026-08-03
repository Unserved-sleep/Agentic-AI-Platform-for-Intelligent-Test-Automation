"""
======================================================================

Module:
Browser State Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Captures the full observable state of a browser at a
specific point in time during execution.

BrowserState is a read-only snapshot. It does not hold
any Playwright objects and can be safely serialised to
JSON or stored in a database.

Fields Captured
---------------
- current_url      — Full URL of the active page
- title            — Page title (document.title)
- cookies          — All cookies in the current context
- viewport         — Viewport dimensions (width x height)
- local_storage    — Contents of window.localStorage
- session_storage  — Contents of window.sessionStorage
- user_agent       — Browser user-agent string

----------------------------------------------------------------------

TODO:
Support geolocation and permission state.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Captured by PageContext inside the MCP layer.
Returned as part of ExecutionResult metadata.

======================================================================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ViewportSize(BaseModel):
    """Viewport dimensions in pixels."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    width: int = Field(
        ...,
        ge=1,
        description="Viewport width in pixels.",
    )

    height: int = Field(
        ...,
        ge=1,
        description="Viewport height in pixels.",
    )


class BrowserState(BaseModel):
    """
    Immutable snapshot of the browser state at a point
    in time.

    All fields are read-only after construction.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    current_url: str = Field(
        ...,
        description="Full URL of the active page at capture time.",
    )

    title: str = Field(
        default="",
        description="Page title (document.title).",
    )

    cookies: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "All cookies present in the browser context at "
            "capture time. Each entry is a dict matching the "
            "Playwright cookie schema."
        ),
    )

    viewport: ViewportSize | None = Field(
        default=None,
        description="Viewport dimensions.",
    )

    local_storage: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Key/value contents of window.localStorage at "
            "capture time."
        ),
    )

    session_storage: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Key/value contents of window.sessionStorage at "
            "capture time."
        ),
    )

    user_agent: str = Field(
        default="",
        description="Browser user-agent string.",
    )

    captured_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this state was captured.",
    )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_cookie(self, name: str) -> dict[str, Any] | None:
        """
        Return the first cookie matching *name*, or None.

        Parameters
        ----------
        name:
            Cookie name to look up.

        Returns
        -------
        dict | None
        """
        for cookie in self.cookies:
            if cookie.get("name") == name:
                return cookie
        return None

    def has_local_storage_key(self, key: str) -> bool:
        """
        Return True if *key* exists in localStorage.

        Parameters
        ----------
        key:
            localStorage key to check.

        Returns
        -------
        bool
        """
        return key in self.local_storage

    def has_session_storage_key(self, key: str) -> bool:
        """
        Return True if *key* exists in sessionStorage.

        Parameters
        ----------
        key:
            sessionStorage key to check.

        Returns
        -------
        bool
        """
        return key in self.session_storage
