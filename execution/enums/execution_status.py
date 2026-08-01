"""
======================================================================

Module:
Execution Status Enum

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines all valid execution statuses for the execution engine.

Using enums prevents magic strings and ensures consistent
status handling across execution, reporting, dashboard,
and deployment modules.

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

from enum import Enum


class ExecutionStatus(str, Enum):
    """
    Represents the lifecycle status of a test execution.
    """

    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"

    PASSED = "PASSED"
    FAILED = "FAILED"

    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"

    SKIPPED = "SKIPPED"