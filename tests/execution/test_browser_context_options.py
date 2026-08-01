from pathlib import Path

from execution.models.browser_context_options import (
    BrowserContextOptions,
)


def test_browser_context_options():

    options = BrowserContextOptions(
        record_video=True,
        video_directory=Path("videos"),
        viewport_width=1920,
        viewport_height=1080,
    )

    playwright_options = options.to_playwright_dict()

    assert playwright_options["record_video_dir"] == "videos"

    assert playwright_options["viewport"]["width"] == 1920

    assert playwright_options["viewport"]["height"] == 1080