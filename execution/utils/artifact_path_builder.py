"""
======================================================================

Module:
Artifact Path Builder

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Builds standardized artifact directories and file paths.

All execution artifacts must use this class to ensure
consistent storage across the platform.

----------------------------------------------------------------------

TODO:
Support configurable artifact root directory.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by all artifact collectors.

======================================================================
"""

from pathlib import Path


class ArtifactPathBuilder:
    """
    Builds standardized artifact directories.
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts",
    ) -> None:

        self.artifacts_root = Path(artifacts_root)

    def execution_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.artifacts_root / run_id

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def screenshot_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.execution_directory(run_id) / "screenshots"

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def trace_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.execution_directory(run_id) / "traces"

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def video_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.execution_directory(run_id) / "videos"

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def log_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.execution_directory(run_id) / "logs"

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def report_directory(
        self,
        run_id: str,
    ) -> Path:

        path = self.execution_directory(run_id) / "reports"

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path