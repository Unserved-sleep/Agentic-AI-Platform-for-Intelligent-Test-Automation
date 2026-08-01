"""
======================================================================

Module:
Browser Factory

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Creates browser manager implementations.

The factory injects the shared PlaywrightEngine into each
browser manager.

======================================================================
"""

from execution.browser.playwright_browser_manager import PlaywrightBrowserManager
from execution.browser.playwright_engine import PlaywrightEngine
from execution.enums import BrowserType


class BrowserFactory:

    @staticmethod
    def create(
        engine: PlaywrightEngine,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = False,
    ) -> PlaywrightBrowserManager:

        return PlaywrightBrowserManager(
            engine=engine,
            browser_type=browser_type,
            headless=headless,
        )