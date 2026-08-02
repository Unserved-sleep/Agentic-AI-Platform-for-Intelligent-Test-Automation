import pytest
from playwright.sync_api import request
import json

class DocumentPage:
    pass

@pytest.fixture
def page():
    pass  # Not needed for API tests

def test_api_invalid_file_type():
    # Define the API endpoint and the invalid file type
    endpoint = "/api/documents"
    file_type = "application/x-msdownload"  # EXE file type

    # Create a sample request payload with an EXE file attached
    payload = {
        "filename": "example.exe",
        "file": "VGhlbiBpcyBhIHZhcmlldCB2YXJpYWJsZQ=="  # Sample EXE file content as base64
    }

    # Send the POST request with the EXE file attached
    response = request.post(
        endpoint,
        headers={
            "Content-Type": file_type
        },
        data=payload
    )

    # Verify the HTTP status code
    assert response.status == 400
    assert response.headers["content-type"] == "application/json"

    # Verify the response body
    response_body = json.loads(response.body())
    assert "error" in response_body
    assert response_body["error"] == "Invalid file type"