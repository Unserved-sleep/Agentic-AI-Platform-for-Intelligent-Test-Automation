"""
======================================================================

Module:
Execution Type Enum

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the supported execution modes for the platform.

Execution types determine which runner should execute
the request.

----------------------------------------------------------------------

TODO:
None

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
ENGINEER 2

Engineer 2 will eventually specify which execution type
(UI, API or Hybrid) is required.

======================================================================
"""

from enum import Enum


class ExecutionType(str, Enum):
    """
    Supported execution types.
    """

    UI = "UI"
    API = "API"
    HYBRID = "HYBRID"