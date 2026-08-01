"""
======================================================================
MODEL_VERSION = "1.0.0"

Module:
Execution Request Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a standardized execution request for the Execution Engine.

This model is the ONLY request object accepted by the execution layer.

Any output received from Engineer 2 MUST first be converted into this
model through an Adapter before entering the execution pipeline.

----------------------------------------------------------------------

TODO:
None

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION (ENGINEER 2)

Status:
Pending

Expected:
Engineer 2 will generate Playwright scripts and metadata.

Their output MUST be converted into ExecutionRequest by an adapter.

======================================================================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from execution.enums import ExecutionType

class ExecutionRequest(BaseModel):
    """
    Standard execution request consumed by the Execution Engine.

    This model is intentionally independent of the output of any AI
    agent so that future changes in Engineer 2's implementation do not
    affect the execution layer.
    """
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        frozen=False
    )

    run_id: str = Field(
        ...,
        description="Unique execution identifier."
    )

    execution_type: ExecutionType = Field(
        ...,
        description="Execution type."
    )

    script_path: str = Field(
        ...,
        description="Path to Playwright script."
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata."
    )

    environment: str = Field(
        default="local",
        description="Execution environment."
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Execution tags."
    )

    timeout: int = Field(
        default=300,
        ge=1,
        description="Maximum execution timeout in seconds."
    )

    retries: int = Field(
        default=0,
        ge=0,
        description="Retry count."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp."
    )