import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def request():
    return APIRequestContext()

@pytest.fixture
def db_session():
    # Assume this fixture is defined elsewhere
    pass

def test_ts_006(request: APIRequestContext, db_session):
    # Send a POST request to /api/documents without being authenticated
    response = request.post("/api/documents")

    # Verify the request is rejected with a 401 Unauthorized status code
    assert response.status == 401

    # Verify backend database state
    assert not db_asserter.verify_document_ingested(db_session, "any_filename")