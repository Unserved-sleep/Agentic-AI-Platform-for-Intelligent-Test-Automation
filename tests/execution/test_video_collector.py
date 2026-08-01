from uuid import uuid4

from execution.collectors.video_collector import VideoCollector


def test_build_context_options():

    collector = VideoCollector()

    options = collector.build_context_options(
        run_id=str(uuid4()),
    )

    assert options.record_video is True

    assert options.video_directory is not None