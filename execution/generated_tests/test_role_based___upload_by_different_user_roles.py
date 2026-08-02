import pytest
from playwright.sync_api import request
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # Assuming a DB session fixture exists or instantiate it
    # For demonstration purposes, we'll use a mock session
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return None
    return MockSession()

def test_role_based_upload_by_different_user_roles(request, db_session):
    # Define valid documents for admin and regular users
    admin_doc = {"filename": "admin_document.pdf", "content": "Admin document content"}
    regular_doc = {"filename": "regular_document.pdf", "content": "Regular document content"}

    # Define headers for admin and regular users
    admin_headers = {"Authorization": "Bearer admin_token"}
    regular_headers = {"Authorization": "Bearer regular_token"}

    # Send a POST request to /api/documents with a valid document attached as an admin user
    admin_response = request.post("/api/documents", headers=admin_headers, data=admin_doc)
    assert admin_response.status == 201

    # Send a POST request to /api/documents with a valid document attached as a regular user
    regular_response = request.post("/api/documents", headers=regular_headers, data=regular_doc)
    assert regular_response.status == 201

    # Verify the database state using the DBAssertionHelper
    assert db_asserter.verify_document_ingested(db_session, admin_doc["filename"])
    assert db_asserter.verify_document_ingested(db_session, regular_doc["filename"])