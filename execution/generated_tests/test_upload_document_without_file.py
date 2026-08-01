import pytest
from playwright.sync_api import request

@pytest.fixture
def api_request():
    return request

def test_upload_document_without_file(api_request):
    response = api_request.post("http://localhost:8000/api/documents")
    assert response.status == 400

def test_upload_document_without_file_json_schema(api_request):
    response = api_request.post("http://localhost:8000/api/documents")
    assert response.status == 400
    assert "error" in response.json()

def test_upload_document_without_file_headers(api_request):
    response = api_request.post("http://localhost:8000/api/documents")
    assert response.status == 400
    assert "Content-Type" in response.headers