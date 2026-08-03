import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter
from unittest.mock import MagicMock

@pytest.fixture
def api_request_context():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        api_context = context.request
        yield api_context
        browser.close()

@pytest.fixture
def db_session():
    # Assuming db_session fixture is defined elsewhere
    pass

def test_upload_document(api_request_context: APIRequestContext, db_session):
    document_name = "test_document.pdf"
    file_path = f"files/{document_name}"
    with open(file_path, "rb") as file:
        response = api_request_context.post("/api/documents", 
                                             headers={"Content-Type": "multipart/form-data"}, 
                                             data={"document": (file_path, file, "application/pdf")})
    assert response.status == 201
    assert db_asserter.verify_document_ingested(db_session, document_name)