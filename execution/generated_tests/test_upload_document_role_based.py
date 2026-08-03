import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # Initialize a database session
    pass

def test_upload_document_role_based(db_session):
    # Create APIRequestContext as an admin user
    admin_request = APIRequestContext(base_url="http://localhost:8080", extra_http_headers={"role": "admin"})

    # Send a POST request to /api/documents with a multipart/form-data payload containing a file as an admin user
    admin_response = admin_request.post("/api/documents", data={"file": ("document.txt", "Hello World!", "text/plain")})
    assert admin_response.status == 201

    # Verify that a Document record is persisted in the database for the admin user
    assert db_asserter.verify_document_ingested(db_session, "document.txt")

    # Create APIRequestContext as a regular user
    regular_request = APIRequestContext(base_url="http://localhost:8080", extra_http_headers={"role": "regular"})

    # Send a POST request to /api/documents with a multipart/form-data payload containing a file as a regular user
    regular_response = regular_request.post("/api/documents", data={"file": ("document.txt", "Hello World!", "text/plain")})
    assert regular_response.status == 201

    # Verify that a Document record is persisted in the database for the regular user
    assert db_asserter.verify_document_ingested(db_session, "document.txt")