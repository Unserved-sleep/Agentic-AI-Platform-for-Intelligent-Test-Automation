"""
======================================================================

Module:
Video Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Provides Playwright video recording configuration and
collects recorded video artifacts after execution.

----------------------------------------------------------------------

TODO:
Support configurable video resolution.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by PlaywrightUIRunner before browser launch and after
execution completion.

======================================================================
"""

from pathlib import Path

from playwright.sync_api import BrowserContext

from execution.enums import ArtifactType
from execution.models.artifact import Artifact
from execution.utils.artifact_path_builder import ArtifactPathBuilder


class VideoCollector:
    """
    Handles Playwright video recording.
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts",
    ) -> None:

        self.path_builder = ArtifactPathBuilder(
            artifacts_root=artifacts_root,
        )

    def context_options(
        self,
        run_id: str,
    ) -> dict:
        """
        Build BrowserContext options required for
        Playwright video recording.
        """

        video_directory = self.path_builder.video_directory(
            run_id
        )

        return {
            "record_video_dir": str(video_directory),
        }

    def collect(
        self,
        page,
        run_id: str,
    ) -> Artifact:
        """
        Retrieve recorded Playwright video.
        """

        page.context.close()

        video = page.video

        if video is None:
            raise RuntimeError(
                "No Playwright video was recorded."
            )

        video_path = Path(video.path())

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        return Artifact(
            name=video_path.name,
            path=video_path,
            artifact_type=ArtifactType.VIDEO,
            size_bytes=video_path.stat().st_size,
        )