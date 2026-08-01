"""
======================================================================

Module:
Trace Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Starts and stops Playwright tracing.

Generated trace archives are stored as execution artifacts.

----------------------------------------------------------------------

TODO:
Support configurable trace options.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by ArtifactCollector and PlaywrightUIRunner.

======================================================================
"""

from playwright.sync_api import BrowserContext

from execution.enums import ArtifactType
from execution.models.artifact import Artifact
from execution.utils.artifact_path_builder import ArtifactPathBuilder


class TraceCollector:
    """
    Collects Playwright trace artifacts.
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts",
    ) -> None:

        self.path_builder = ArtifactPathBuilder(
            artifacts_root=artifacts_root,
        )

    def start(
        self,
        context: BrowserContext,
    ) -> None:
        """
        Start Playwright tracing.
        """

        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

    def stop(
        self,
        run_id: str,
        context: BrowserContext,
        filename: str = "trace.zip",
    ) -> Artifact:
        """
        Stop tracing and save the trace archive.
        """

        trace_directory = self.path_builder.trace_directory(run_id)

        trace_path = trace_directory / filename

        context.tracing.stop(
            path=str(trace_path),
        )

        if not trace_path.exists():
            raise FileNotFoundError(
                f"Trace archive was not created: {trace_path}"
            )

        return Artifact(
            name=filename,
            path=trace_path,
            artifact_type=ArtifactType.TRACE,
            size_bytes=trace_path.stat().st_size,
        )