from execution.collectors.log_collector import LogCollector
from execution.models.log_entry import LogEntry


def test_log_collector():

    collector = LogCollector()

    collector._logs.append(
        LogEntry(
            level="INFO",
            source="Browser",
            message="Hello",
        )
    )

    logs = collector.collect()

    assert len(logs) == 1

    assert logs[0].message == "Hello"

    collector.clear()

    assert collector.collect() == []