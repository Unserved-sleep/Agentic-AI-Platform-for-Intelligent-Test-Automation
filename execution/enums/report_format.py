"""
======================================================================

Module:
Report Format Enum

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the supported report output formats.

----------------------------------------------------------------------

TODO:
Support Allure reports in future.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from enum import Enum


class ReportFormat(str, Enum):
    """
    Supported report formats.
    """

    HTML = "html"
    PDF = "pdf"
    JSON = "json"