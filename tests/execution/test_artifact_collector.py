from unittest.mock import MagicMock

from execution.collectors.artifact_collector import ArtifactCollector


def test_artifact_collector():

    screenshot = MagicMock()
    trace = MagicMock()
    video = MagicMock()
    logs = MagicMock()

    screenshot.collect.return_value = MagicMock()
    trace.collect.return_value = MagicMock()
    video.collect.return_value = MagicMock()
    logs.collect.return_value = []

    collector = ArtifactCollector(
        screenshot_collector=screenshot,
        trace_collector=trace,
        video_collector=video,
        log_collector=logs,
    )

    session = MagicMock()

    bundle = collector.collect(session)

    assert bundle is not None

    assert len(bundle.screenshots) == 1
    assert len(bundle.traces) == 1
    assert len(bundle.videos) == 1
    assert len(bundle.logs) == 0