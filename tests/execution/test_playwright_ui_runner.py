from uuid import uuid4
from unittest.mock import MagicMock

from execution.collectors.artifact_collector import ArtifactCollector
from execution.enums import ExecutionStatus, ExecutionType
from execution.runners.playwright_ui_runner import PlaywrightUIRunner
from execution.models.execution_request import ExecutionRequest


def test_ui_runner():

    # Arrange
    browser_manager = MagicMock()
    artifact_collector = MagicMock(spec=ArtifactCollector)

    session = MagicMock()
    session.page = MagicMock()

    browser_manager.launch.return_value = session
    artifact_collector.collect.return_value = MagicMock()

    runner = PlaywrightUIRunner(
        browser_manager=browser_manager,
        artifact_collector=artifact_collector,
    )

    request = ExecutionRequest(
        run_id=str(uuid4()),
        execution_type=ExecutionType.UI,
        script_path="tests/dummy.py",
    )

    def dummy_test(page):
        assert page is session.page

    # Act
    result = runner.execute(
        request=request,
        test_function=dummy_test,
    )

    # Assert
    assert result.status == ExecutionStatus.PASSED

    browser_manager.launch.assert_called_once()

    artifact_collector.collect.assert_called_once_with(
        session=session,
    )

    browser_manager.close.assert_called_once_with(
        session,
    )


def test_ui_runner_failure():

    browser_manager = MagicMock()
    artifact_collector = MagicMock(spec=ArtifactCollector)

    session = MagicMock()
    session.page = MagicMock()

    browser_manager.launch.return_value = session
    artifact_collector.collect.return_value = MagicMock()

    runner = PlaywrightUIRunner(
        browser_manager=browser_manager,
        artifact_collector=artifact_collector,
    )

    request = ExecutionRequest(
        run_id=str(uuid4()),
        execution_type=ExecutionType.UI,
        script_path="tests/dummy.py",
    )

    def failing_test(page):
        raise RuntimeError("Intentional failure")

    result = runner.execute(
        request=request,
        test_function=failing_test,
    )

    assert result.status == ExecutionStatus.FAILED
    assert "Intentional failure" in result.error_message

    artifact_collector.collect.assert_called_once_with(
        session=session,
    )

    browser_manager.close.assert_called_once_with(
        session,
    )