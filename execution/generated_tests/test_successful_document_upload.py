import pytest
from playwright.sync_api import Page
from database.assertions import db_asserter
from typing import Generator

# Define a fixture for the database session
@pytest.fixture
def db_session():
    # Replace this with your actual database session setup code
    # For this example, we'll assume a simple in-memory database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    return Session()

def test_successful_document_upload(page: Page, db_session: Generator):
    # Define a valid file
    file_path = "path/to/valid/file.txt"
    filename = "file.txt"

    # Send a POST request to /api/documents with a valid file attached
    with page.request.post("http://localhost:8000/api/documents", 
                            files={"file": file_path}) as response:
        # Verify the request returns a 201 Created status code
        assert response.status == 201

    # Check the database for a newly created Document record with the correct filename
    assert db_asserter.verify_document_ingested(db_session, filename)