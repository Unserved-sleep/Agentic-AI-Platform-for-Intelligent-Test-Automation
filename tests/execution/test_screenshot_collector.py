from uuid import uuid4

from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.collectors.screenshot_collector import ScreenshotCollector
from execution.enums import BrowserType


def test_screenshot_collector():

    engine = PlaywrightEngine()
    engine.start()

    try:

        manager = BrowserFactory.create(
            engine=engine,
            browser_type=BrowserType.CHROMIUM,
        )

        session = manager.launch()

        session.page.goto("https://example.com")

        collector = ScreenshotCollector()

        artifact = collector.collect(
            run_id=str(uuid4()),
            page=session.page,
        )

        assert artifact.path.exists()

        assert artifact.path.suffix == ".png"

        assert artifact.size_bytes > 0

        manager.close(session)

    finally:

        engine.stop()