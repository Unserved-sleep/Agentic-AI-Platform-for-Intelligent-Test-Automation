from uuid import uuid4

from execution.enums import ExecutionStatus, ExecutionType
from execution.models.execution_request import ExecutionRequest
from execution.services.execution_service import ExecutionService


def test_execution_service():

    service = ExecutionService()

    request = ExecutionRequest(
        run_id=str(uuid4()),
        execution_type=ExecutionType.UI,
        script_path="tests/dummy.py",
    )

    def dummy_test(page):
        page.set_content("<h1>Hello World</h1>")

    result = service.execute(
        request=request,
        test_function=dummy_test,
    )

    assert result.status == ExecutionStatus.PASSED