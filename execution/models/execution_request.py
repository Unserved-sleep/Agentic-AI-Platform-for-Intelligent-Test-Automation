"""
======================================================================
MODEL_VERSION = "2.0.0"

Module:
Execution Request Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a standardized execution request for the Execution Engine.

This model is the ONLY request object accepted by the execution layer.

It contains execution configuration only.

The actual Playwright test/function/script is supplied separately by the
caller (Engineer 2, Script Provider, API, etc.).

----------------------------------------------------------------------

TODO:
Introduce ExecutionEnvironment enum.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION (ENGINEER 2)

Engineer 2 may generate Playwright code using AI agents.

Their generated function/object is NOT stored inside this model.

ExecutionRequest only describes HOW execution should happen.

======================================================================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from execution.enums import BrowserType
from execution.enums import ExecutionType


class ExecutionRequest(BaseModel):
    """
    Standard execution request consumed by the Execution Engine.

    This model intentionally contains execution configuration only.

    It is independent of:

    - AI Agent outputs
    - Playwright source code
    - Script files
    - Callable objects

    This keeps the execution layer loosely coupled to upstream agents.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        frozen=False,
    )

    run_id: str = Field(
        ...,
        description="Unique execution identifier.",
    )

    execution_type: ExecutionType = Field(
        ...,
        description="Execution type.",
    )

    browser_type: BrowserType = Field(
        default=BrowserType.CHROMIUM,
        description="Browser used during execution.",
    )

    headless: bool = Field(
        default=True,
        description="Run browser in headless mode.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata.",
    )

    environment: str = Field(
        default="local",
        description="Execution environment.",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Execution tags.",
    )

    timeout: int = Field(
        default=300,
        ge=1,
        description="Execution timeout in seconds.",
    )

    retries: int = Field(
        default=0,
        ge=0,
        description="Maximum retry attempts.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp.",
    )