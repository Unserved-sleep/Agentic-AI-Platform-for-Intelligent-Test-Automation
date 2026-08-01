"""
======================================================================

Module:
Execution Result Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents the final outcome of an execution.

This model is returned by every execution runner and is
consumed by the Dashboard, Report Generator and future
integration modules.

----------------------------------------------------------------------

TODO:
Support execution metrics and resource utilization.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from execution.enums import ExecutionStatus
from execution.models.artifact_bundle import ArtifactBundle


class ExecutionResult(BaseModel):
    """
    Represents the outcome of a single execution.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

    run_id: str = Field(
        ...,
        description="Unique execution identifier."
    )

    status: ExecutionStatus = Field(
        ...,
        description="Final execution status."
    )

    artifacts: ArtifactBundle = Field(
        default_factory=ArtifactBundle,
        description="Artifacts produced during execution."
    )

    started_at: datetime = Field(
        ...,
        description="Execution start time."
    )

    completed_at: datetime = Field(
        ...,
        description="Execution completion time."
    )

    error_message: str | None = Field(
        default=None,
        description="Execution error message."
    )

    stack_trace: str | None = Field(
        default=None,
        description="Stack trace for unexpected failures."
    )