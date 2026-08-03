import pytest
from database.assertions import db_asserter
from playwright.sync_api import APIRequestContext

@pytest.fixture
def api_request_context():
    return APIRequestContext(base_url="http://localhost:8080")

def test_TS_001_upload_document_via_api(api_request_context, db_session):
    file_path = "path/to/test/document.pdf"
    file_name = "document.pdf"
    with api_request_context.post("/api/documents",
                                  headers={"Content-Type": "multipart/form-data"},
                                  data={"file": (file_path, file_name)}) as response:
        assert response.status == 201
        assert db_asserter.verify_document_ingested(db_session, file_name)