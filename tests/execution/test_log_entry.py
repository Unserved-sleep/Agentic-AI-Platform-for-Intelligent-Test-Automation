from execution.models.log_entry import LogEntry


def test_log_entry():

    log = LogEntry(
        level="INFO",
        source="Browser",
        message="Browser launched successfully.",
    )

    assert log.level == "INFO"
    assert log.source == "Browser"
    assert log.message == "Browser launched successfully."