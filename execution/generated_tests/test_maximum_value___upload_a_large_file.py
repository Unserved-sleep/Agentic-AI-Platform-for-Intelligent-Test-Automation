import pytest
from playwright.sync_api import Page
from database.assertions import db_asserter
import requests

def test_upload_large_file(test_client, db_session):
    # Create a large file for uploading
    large_file = open("large_file.txt", "w")
    for _ in range(1000000):
        large_file.write("Hello, World!")
    large_file.close()

    # Send a POST request to /api/documents with the large file attached
    files = {"file": open("large_file.txt", "rb")}
    response = test_client.post("/api/documents", files=files)

    # Verify the HTTP status code
    assert response.status_code == 201

    # Verify the document record persisted in the database
    assert db_asserter.verify_document_ingested(db_session, "large_file.txt")

    # Clean up
    import os
    os.remove("large_file.txt")

@pytest.fixture
def test_client():
    # Assume this fixture creates a test client with the correct authentication and API endpoint
    return requests.Session()

@pytest.fixture
def db_session():
    # Assume this fixture creates a database session
    # You may need to import the necessary database library (e.g., sqlalchemy) and create a session
    # For example:
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///example.db")
    Session = sessionmaker(bind=engine)
    return Session()