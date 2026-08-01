from uuid import uuid4

from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.collectors.trace_collector import TraceCollector
from execution.enums import BrowserType


def test_trace_collector():

    engine = PlaywrightEngine()
    engine.start()

    try:

        manager = BrowserFactory.create(
            engine=engine,
            browser_type=BrowserType.CHROMIUM,
        )

        session = manager.launch()

        collector = TraceCollector()

        collector.start(session.context)

        session.page.goto("https://example.com")

        artifact = collector.stop(
            run_id=str(uuid4()),
            context=session.context,
        )

        assert artifact.path.exists()

        assert artifact.path.suffix == ".zip"

        assert artifact.size_bytes > 0

        manager.close(session)

    finally:

        engine.stop()