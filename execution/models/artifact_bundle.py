"""
======================================================================

Module:
Artifact Bundle Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents all artifacts generated during a single execution.

Bundles screenshots, traces, logs, videos and reports into
one object that can be passed throughout the execution
pipeline.

----------------------------------------------------------------------

TODO:
Support execution metrics and HAR files.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from pydantic import BaseModel, ConfigDict, Field

from execution.models.artifact import Artifact


class ArtifactBundle(BaseModel):
    """
    Collection of artifacts produced by one execution.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

    screenshots: list[Artifact] = Field(
        default_factory=list,
        description="Execution screenshots."
    )

    traces: list[Artifact] = Field(
        default_factory=list,
        description="Execution trace files."
    )

    videos: list[Artifact] = Field(
        default_factory=list,
        description="Execution recordings."
    )

    logs: list[Artifact] = Field(
        default_factory=list,
        description="Execution logs."
    )

    reports: list[Artifact] = Field(
        default_factory=list,
        description="Generated execution reports."
    )