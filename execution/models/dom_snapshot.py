"""
======================================================================

Module:
DOM Snapshot Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a point-in-time snapshot of a page's DOM.

DOM snapshots are useful for:
- Debugging test failures (diff the DOM before/after)
- Feeding page content to AI failure analysis
- Archiving page structure for regression detection

Fields
------
- url           — Page URL at snapshot time
- html          — Full page HTML (outerHTML of document)
- text_content  — Plain text content (optional, stripped HTML)
- timestamp     — UTC time the snapshot was taken
- run_id        — Execution run this snapshot belongs to

----------------------------------------------------------------------

TODO:
Support partial DOM capture (selector-scoped snapshots).
Support accessibility tree snapshots.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Captured by PageContext inside the MCP layer.
May be attached to ExecutionResult for AI diagnostics.

======================================================================
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DOMSnapshot(BaseModel):
    """
    Point-in-time snapshot of a page's DOM.

    All fields are read-only after construction.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    url: str = Field(
        ...,
        description="URL of the page when this snapshot was taken.",
    )

    html: str = Field(
        ...,
        description="Full HTML of the page (document.documentElement.outerHTML).",
    )

    text_content: str = Field(
        default="",
        description=(
            "Plain-text content of the page (optional). "
            "Populated from document.body.innerText when captured."
        ),
    )

    run_id: str = Field(
        default="",
        description=(
            "Unique execution run identifier this snapshot "
            "belongs to. Set by the collector."
        ),
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this snapshot was taken.",
    )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def size_bytes(self) -> int:
        """
        Approximate size of the HTML string in bytes.

        Returns
        -------
        int
        """
        return len(self.html.encode("utf-8"))

    def contains_text(self, text: str) -> bool:
        """
        Return True if *text* appears anywhere in the page
        text content (case-insensitive).

        Parameters
        ----------
        text:
            Substring to search for.

        Returns
        -------
        bool
        """
        return text.lower() in self.text_content.lower()

    def contains_html(self, fragment: str) -> bool:
        """
        Return True if *fragment* appears anywhere in the
        raw HTML (case-insensitive).

        Parameters
        ----------
        fragment:
            HTML fragment to search for.

        Returns
        -------
        bool
        """
        return fragment.lower() in self.html.lower()
