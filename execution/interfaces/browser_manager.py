"""
======================================================================

Module:
Browser Manager Interface

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the contract for browser lifecycle management.

Every browser implementation (Playwright, Selenium,
Browserless, etc.) must implement this interface.

----------------------------------------------------------------------

Dependencies:
- BrowserSession

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

from abc import ABC, abstractmethod

from execution.models.browser_session import BrowserSession


class BrowserManager(ABC):
    """
    Abstract interface for browser lifecycle management.
    """

    @abstractmethod
    def launch(self) -> BrowserSession:
        """
        Launch a browser session.

        Returns
        -------
        BrowserSession
            Active browser session.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self, session: BrowserSession) -> None:
        """
        Close the provided browser session.
        """
        raise NotImplementedError

    @abstractmethod
    def is_alive(self, session: BrowserSession) -> bool:
        """
        Check whether the browser session is active.
        """
        raise NotImplementedError