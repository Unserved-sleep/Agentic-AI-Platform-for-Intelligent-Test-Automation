import pytest
from playwright.sync_api import APIRequestContext

@pytest.fixture
def api_request():
    return APIRequestContext()

def test_upload_with_invalid_state(api_request):
    # Put the system into an invalid state (e.g., maintenance mode)
    maintenance_mode_response = api_request.post("/api/maintenance-mode")
    assert maintenance_mode_response.status == 200

    # Send a POST request to /api/documents with a valid file attached in the request body as multipart/form-data
    file = {"document": ("example.txt", "example content", "text/plain")}
    response = api_request.post("/api/documents", multipart.formData(file))

    # Verify the request returns an error status code (e.g., 503 Service Unavailable)
    assert response.status == 503

    # Verify the response content
    assert response.json() == {"error": "Service Unavailable"}