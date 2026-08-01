from uuid import uuid4

from execution.browser.browser_factory import BrowserFactory
from execution.browser.playwright_engine import PlaywrightEngine
from execution.enums import BrowserType, ExecutionType
from execution.models.execution_request import ExecutionRequest
from execution.runners.playwright_ui_runner import PlaywrightUIRunner


def demo_test(page):
    page.goto("https://example.com")
    assert page.title() == "Example Domain"


def test_ui_runner():

    engine = PlaywrightEngine()
    engine.start()

    try:

        manager = BrowserFactory.create(
            engine=engine,
            browser_type=BrowserType.CHROMIUM,
        )

        runner = PlaywrightUIRunner(manager)

        request = ExecutionRequest(
            run_id=str(uuid4()),
            execution_type=ExecutionType.UI,
        )

        result = runner.execute(
            request,
            demo_test,
        )

        assert result.status.value == "PASSED"

    finally:

        engine.stop()