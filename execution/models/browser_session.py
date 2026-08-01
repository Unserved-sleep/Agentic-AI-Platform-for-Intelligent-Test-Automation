"""
======================================================================

Module:
Browser Session Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a single browser execution session.

The BrowserSession is the central execution object shared
across the Browser Manager, Execution Runner and Artifact
Collectors.

----------------------------------------------------------------------

TODO:
Support browser storage state and execution metadata.

----------------------------------------------------------------------

DUMMY:
video_directory is None until VideoCollector integration.

----------------------------------------------------------------------

INTEGRATION:
Shared across all execution components.

======================================================================
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from execution.enums import BrowserType
from execution.models.artifact import Artifact

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class BrowserSession(BaseModel):
    """
    Represents an active browser execution session.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="forbid",
    )

    session_id: str = Field(
        ...,
        description="Unique browser session identifier.",
    )

    browser_type: BrowserType = Field(
        ...,
        description="Browser used for execution.",
    )

    browser: Any = Field(
        ...,
        description="Playwright browser instance.",
    )

    context: Any = Field(
        ...,
        description="Playwright browser context.",
    )

    page: Any = Field(
        ...,
        description="Active Playwright page.",
    )

    is_active: bool = Field(
        default=True,
        description="Whether the browser session is active.",
    )

    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time.",
    )

    video_directory: Path | None = Field(
        default=None,
        description="Directory where Playwright stores videos.",
    )

    artifacts: list[Artifact] = Field(
        default_factory=list,
        description="Artifacts produced during this execution.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata.",
    )

    def add_artifact(
        self,
        artifact: Artifact,
    ) -> None:
        """
        Register a newly created execution artifact.
        """

        self.artifacts.append(artifact)

    def deactivate(self) -> None:
        """
        Mark this browser session as inactive.
        """

        self.is_active = False