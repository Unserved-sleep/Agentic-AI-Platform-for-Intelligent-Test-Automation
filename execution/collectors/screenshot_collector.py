"""
======================================================================

Module:
Screenshot Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Captures screenshots from Playwright pages.

Screenshots are stored inside the execution artifact
directory and returned as Artifact objects.

----------------------------------------------------------------------

TODO:
Support full-page screenshots and multiple screenshots.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by ArtifactCollector.

======================================================================
"""

from pathlib import Path

from playwright.sync_api import Page

from execution.enums import ArtifactType
from execution.models.artifact import Artifact
from execution.utils.artifact_path_builder import ArtifactPathBuilder


class ScreenshotCollector:
    """
    Captures screenshots from Playwright pages.
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts",
    ) -> None:

        self.artifacts_root = Path(artifacts_root)

    def collect(
        self,
        run_id: str,
        page: Page,
        filename: str = "screenshot.png",
    ) -> Artifact:
        """
        Capture a screenshot.

        Parameters
        ----------
        run_id:
            Execution identifier.

        page:
            Active Playwright page.

        filename:
            Screenshot filename.

        Returns
        -------
        Artifact
        """

        builder = ArtifactPathBuilder()

        screenshot_dir = builder.screenshot_directory(run_id)

        screenshot_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        screenshot_path = screenshot_dir / filename

        page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )
        if not screenshot_path.exists():
            raise FileNotFoundError(
                f"Screenshot was not created: {screenshot_path}"
            )

        return Artifact(
            name=filename,
            path=screenshot_path,
            artifact_type=ArtifactType.SCREENSHOT,
            size_bytes=screenshot_path.stat().st_size,
        )