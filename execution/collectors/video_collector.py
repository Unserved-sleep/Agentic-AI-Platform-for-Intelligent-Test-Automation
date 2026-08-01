"""
======================================================================

Module:
Video Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Builds BrowserContextOptions required for Playwright video
recording and collects generated video artifacts.

----------------------------------------------------------------------

TODO:
Support configurable video size and naming.

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

from execution.enums import ArtifactType
from execution.models.artifact import Artifact
from execution.models.browser_context_options import BrowserContextOptions
from execution.models.browser_session import BrowserSession
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

    def build_context_options(
        self,
        run_id: str,
    ) -> BrowserContextOptions:
        """
        Build BrowserContext options for video recording.
        """

        video_directory = self.path_builder.video_directory(
            run_id,
        )

        return BrowserContextOptions(
            record_video=True,
            video_directory=video_directory,
        )

    def collect(
        self,
        session: BrowserSession,
    ) -> Artifact:
        """
        Collect the recorded Playwright video.
        """

        if session.page.video is None:
            raise RuntimeError(
                "No Playwright video was recorded."
            )

        video_path = Path(
            session.page.video.path()
        )

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        artifact = Artifact(
            name=video_path.name,
            path=video_path,
            artifact_type=ArtifactType.VIDEO,
            size_bytes=video_path.stat().st_size,
        )

        session.add_artifact(
            artifact
        )

        return artifact