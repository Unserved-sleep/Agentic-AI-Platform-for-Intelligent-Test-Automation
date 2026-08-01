import pytest
from playwright.sync_api import request

@pytest.mark.api_contract
def test_upload_without_file(api_request):
    # Send a POST request to /api/documents without a file attached
    response = api_request.post("/api/documents")

    # Verify the status code
    expect(response.status).to_equal(400)