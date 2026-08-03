import pytest
from database.assertions import db_asserter
from playwright.sync_api import APIRequestContext

@pytest.fixture
def db_session():
    # implement db_session fixture
    pass

def test_TS_002(api_request_context: APIRequestContext, db_session: Session):
    file = {"name": "example.pdf", "mimeType": "application/pdf", "buffer": b"PDF file content"}
    response = api_request_context.post("/api/documents", files={"file": file})
    assert response.status == 201
    assert db_asserter.verify_document_ingested(db_session, "example.pdf")