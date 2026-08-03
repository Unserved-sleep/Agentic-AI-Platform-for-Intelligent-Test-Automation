import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # Assuming this fixture is defined elsewhere in the codebase
    # and returns a valid database session object
    pass

def test_upload_document_missing_input(request: APIRequestContext, db_session):
    response = request.post("/api/documents")
    assert response.status == 400
    # Verify backend database state is unchanged
    assert not db_asserter.verify_document_ingested(db_session, "")
    # Verify JSON body
    assert response.json()["error"] == "Missing required file"