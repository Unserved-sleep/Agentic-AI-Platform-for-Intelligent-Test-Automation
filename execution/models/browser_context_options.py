"""
======================================================================

Module:
Browser Context Options

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents configurable Playwright BrowserContext options.

This model replaces raw dictionaries and provides a
strongly typed configuration object for browser execution.

----------------------------------------------------------------------

TODO:
Support locale, permissions, geolocation and storage state.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Shared between BrowserManager and VideoCollector.

======================================================================
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class BrowserContextOptions(BaseModel):
    """
    Configuration used when creating a Playwright BrowserContext.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    record_video: bool = Field(
        default=False,
        description="Enable Playwright video recording.",
    )

    video_directory: Path | None = Field(
        default=None,
        description="Directory where Playwright stores videos.",
    )

    viewport_width: int = Field(
        default=1280,
        ge=1,
        description="Browser viewport width.",
    )

    viewport_height: int = Field(
        default=720,
        ge=1,
        description="Browser viewport height.",
    )

    ignore_https_errors: bool = Field(
        default=False,
        description="Ignore HTTPS certificate errors.",
    )

    def to_playwright_dict(self) -> dict:
        """
        Convert model into Playwright BrowserContext options.
        """

        options = {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "ignore_https_errors": self.ignore_https_errors,
        }

        if (
            self.record_video
            and self.video_directory is not None
        ):
            options["record_video_dir"] = str(
                self.video_directory
            )

        return options