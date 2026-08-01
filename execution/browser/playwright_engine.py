"""
======================================================================

Module:
Playwright Engine

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Manages the lifecycle of the Playwright engine.

This class is responsible for starting and stopping
Playwright. Browser managers use this engine to launch
browser instances.

----------------------------------------------------------------------

TODO:
Support async Playwright implementation in future.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright


class PlaywrightEngine:
    """
    Manages the lifecycle of the Playwright engine.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None

    @property
    def playwright(self) -> Playwright:
        """
        Returns the active Playwright instance.
        """

        if self._playwright is None:
            raise RuntimeError(
                "Playwright engine has not been started."
            )

        return self._playwright

    def start(self) -> None:
        """
        Start Playwright.
        """

        if self._playwright is None:
            self._playwright = sync_playwright().start()

    def stop(self) -> None:
        """
        Stop Playwright.
        """

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    @property
    def is_running(self) -> bool:
        """
        Returns True if Playwright is running.
        """

        return self._playwright is not None