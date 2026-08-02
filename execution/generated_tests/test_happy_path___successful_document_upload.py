import pytest
from playwright.sync_api import request
from database.assertions import db_asserter
from sqlalchemy.orm import Session
from .models import Document

@pytest.fixture
def db_session():
    # Assuming a function to get a database session
    # Replace with actual implementation
    pass

def test_ts_001(request, db_session):
    # Define the document to be uploaded
    document = {"filename": "example.txt", "content": "Hello World"}

    # Send a POST request to /api/documents with a valid document attached
    response = request.post("/api/documents", data={"filename": document["filename"], "content": document["content"]})

    # Verify the HTTP status code
    assert response.status == 201

    # Verify the document is persisted in the database
    assert db_asserter.verify_document_ingested(db_session, document["filename"])