from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.enums import BrowserType


def test_browser_launch():
    engine = PlaywrightEngine()
    engine.start()

    try:
        manager = BrowserFactory.create(
            engine=engine,
            browser_type=BrowserType.CHROMIUM,
        )

        session = manager.launch()

        session.page.goto("https://example.com")

        assert session.is_active
        assert session.page.title() == "Example Domain"

        manager.close(session)

        assert not session.is_active

    finally:
        engine.stop()