import pytest
from playwright.sync_api import request

class Page:
    pass  # No page required for API Tests

@pytest.fixture
def api_request_context():
    return request

def test_upload_document_with_invalid_file_type(api_request_context):
    file_path = "path_to_exe_file.exe"
    response = api_request_context.post(f"http://localhost:8000/api/documents", files={"file": file_path})
    assert response.status == 400

def test_upload_document_with_invalid_file_type_with_url_param(api_request_context):
    base_url = "http://localhost:8000"
    file_path = "path_to_exe_file.exe"
    url = f"{base_url}/api/documents"
    response = api_request_context.post(url, files={"file": file_path})
    assert response.status == 400

def test_upload_document_with_invalid_file_type_with_base_url_param_override(api_request_context):
    base_url = "http://localhost:8000"
    file_path = "path_to_exe_file.exe"
    url = f"{base_url}/api/documents"
    response = api_request_context.post(url, files={"file": file_path}, base_url=base_url)
    assert response.status == 400