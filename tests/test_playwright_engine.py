from execution.browser.playwright_engine import PlaywrightEngine


def test_engine_start_stop():

    engine = PlaywrightEngine()

    assert not engine.is_running

    engine.start()

    assert engine.is_running

    engine.stop()

    assert not engine.is_running