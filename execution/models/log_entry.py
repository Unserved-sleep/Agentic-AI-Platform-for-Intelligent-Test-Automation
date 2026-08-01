"""
======================================================================

Module:
Log Entry Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents a single browser log entry captured during
test execution.

Logs may originate from:
- Browser console
- JavaScript errors
- Network failures
- Execution events

----------------------------------------------------------------------

TODO:
Support log categories and structured metadata.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by LogCollector and ExecutionResult.

======================================================================
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogEntry(BaseModel):
    """
    Represents a single execution log.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Log creation time.",
    )

    level: str = Field(
        ...,
        description="Log severity.",
    )

    source: str = Field(
        ...,
        description="Origin of the log.",
    )

    message: str = Field(
        ...,
        description="Log message.",
    )