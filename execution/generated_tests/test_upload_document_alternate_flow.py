import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def request():
    return APIRequestContext()

@pytest.fixture
def db_session():
    return db_session

def test_upload_document_alternate_flow(request, db_session):
    file_path = "path_to_your_file.pdf"
    with request.post("/api/documents",
        headers={"Content-Type": "multipart/form-data"},
        data={"file": ("file.pdf", open(file_path, "rb"))}
    ) as response:
        assert response.status == 201
        assert db_asserter.verify_document_ingested(db_session, "file.pdf")