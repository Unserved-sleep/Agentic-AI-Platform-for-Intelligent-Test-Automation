"""
======================================================================

Module:
Playwright Browser Manager

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Concrete implementation responsible for launching and
closing Playwright browser sessions.

This class DOES NOT execute tests.
It only manages the browser lifecycle.

----------------------------------------------------------------------

TODO:
Support browser launch options from configuration.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from uuid import uuid4

from execution.browser.playwright_engine import PlaywrightEngine
from execution.enums import BrowserType
from execution.models.browser_session import BrowserSession


class PlaywrightBrowserManager:

    def __init__(
            self,
            engine: PlaywrightEngine,
            browser_type: BrowserType = BrowserType.CHROMIUM,
            headless: bool = False,
    ):

        self.engine = engine
        self.browser_type = browser_type
        self.headless = headless

    def launch(self) -> BrowserSession:

        if not self.engine.is_running:
            raise RuntimeError(
                "PlaywrightEngine must be started before launching a browser."
            )

        launcher = {
            BrowserType.CHROMIUM: self.engine.playwright.chromium,
            BrowserType.FIREFOX: self.engine.playwright.firefox,
            BrowserType.WEBKIT: self.engine.playwright.webkit,
        }

        browser_launcher = launcher.get(self.browser_type)

        if browser_launcher is None:
            raise ValueError(
                f"Unsupported browser type: {self.browser_type}"
            )

        browser = browser_launcher.launch(
            headless=self.headless
        )

        context = browser.new_context()

        page = context.new_page()

        return BrowserSession(
            browser_type=self.browser_type,
            browser=browser,
            context=context,
            page=page,
            session_id=str(uuid4()),
        )

    def close(
        self,
        session: BrowserSession,
    ) -> None:
        """
        Close browser resources.
        """

        if session.context:
            session.context.close()

        if session.browser:
            session.browser.close()

        try:
            if session.context:
                session.context.close()

            if session.browser:
                session.browser.close()

        finally:
            session.is_active = False


    def is_alive(
        self,
        session: BrowserSession,
    ) -> bool:
        """
        Check whether the session is active.
        """

        return session.is_active