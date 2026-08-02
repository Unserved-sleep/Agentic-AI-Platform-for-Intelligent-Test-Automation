import pytest
from playwright.sync_api import request

@pytest.fixture
def api_request():
    return request

def test_api_post_document_without_body(api_request):
    response = api_request.post("/api/documents")
    assert response.status == 400
    assert response.status_text == "Bad Request"