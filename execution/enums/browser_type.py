"""
======================================================================

Module:
Browser Type Enum

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines all browser engines supported by the execution platform.

This enum is used by BrowserManager and BrowserSession to
determine which browser engine should be launched.

----------------------------------------------------------------------

TODO:
Future support for remote/cloud browsers.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from enum import Enum


class BrowserType(str, Enum):
    """
    Supported browser engines.
    """

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"