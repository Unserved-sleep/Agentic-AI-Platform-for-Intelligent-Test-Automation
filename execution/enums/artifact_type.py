"""
======================================================================

Module:
Artifact Type Enum

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines all artifact types that can be generated during
test execution.

Artifacts are later grouped into an ArtifactBundle and
used by the Dashboard and Report Generator.

----------------------------------------------------------------------

TODO:
Support HAR files and performance metrics in future.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from enum import Enum


class ArtifactType(str, Enum):
    """
    Supported execution artifact types.
    """

    SCREENSHOT = "screenshot"
    TRACE = "trace"
    VIDEO = "video"
    LOG = "log"
    REPORT = "report"