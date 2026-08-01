"""
======================================================================

Module:
Browser Session Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents an active browser session during execution.

Stores runtime Playwright objects required by the execution
engine. This model is NOT intended for serialization.

----------------------------------------------------------------------

TODO:
Support multiple pages/tabs per session.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Browser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page

from execution.enums import BrowserType


@dataclass(slots=True)
class BrowserSession:

    browser_type: BrowserType

    browser: Browser

    context: BrowserContext

    page: Page

    session_id: str

    is_active: bool = True