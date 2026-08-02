import pytest
from playwright.sync_api import request

@pytest.fixture
def api_request():
    return request

def test_invalid_input_no_file_provided(api_request):
    # Send a POST request to /api/documents without a file attached
    response = api_request.post("/api/documents")

    # Verify the HTTP status code
    assert response.status == 400

    # Verify the response contains "Bad Request"
    assert "Bad Request" in response.statusText