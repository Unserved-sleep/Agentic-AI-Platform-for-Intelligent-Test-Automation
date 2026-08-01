"""
======================================================================

Module:
Artifact Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a single artifact generated during test execution.

Artifacts include:
- Screenshot
- Trace
- Video
- Log
- Report

----------------------------------------------------------------------

TODO:
None

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from execution.enums import ReportFormat, ArtifactType


class Artifact(BaseModel):
    """
    Represents a single execution artifact.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

    name: str = Field(
        ...,
        description="Artifact name."
    )

    path: Path = Field(
        ...,
        description="Artifact file path."
    )

    artifact_type: ArtifactType = Field(
        ...,
        description="Type of execution artifact."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    size_bytes: int = Field(
        default=0,
        ge=0
    )

    report_format: ReportFormat | None = Field(
        default=None,
        description="Applicable only for report artifacts."
    )