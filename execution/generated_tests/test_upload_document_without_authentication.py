import pytest
from playwright.sync_api import request

@pytest.fixture
def request_context():
    # Create a new request context without authentication
    request_context = request.RequestContext()
    return request_context

def test_upload_document_without_authentication(request_context):
    # Send a POST request to /api/documents with a valid document
    with request_context as context:
        response = context.post(
            "/api/documents",
            headers={
                "Content-Type": "application/json"
            },
            data={
                "filename": "example.txt",
                "content": "Hello World!"
            }
        )
        # Verify the status code is 401 Unauthorized
        assert response.status == 401