import pytest
from playwright.sync_api import request
from database.assertions import db_asserter
from database.models import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define a test function for the scenario
@pytest.fixture
def db_session():
    # Replace the database URL with your actual database connection string
    engine = create_engine('postgresql://user:password@localhost/dbname')
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_upload_largest_allowed_file_size(request, db_session):
    # Search for maximum file size using search_knowledge_base
    search_response = request.get("/search_knowledge_base")
    assert search_response.status == 200

    # Extract the maximum file size from the response
    max_file_size = int(search_response.json()["max_file_size"])

    # Create a file with the largest allowed size
    file = {"file": ("largest_file.txt", b"a" * max_file_size, "text/plain")}

    # Send a POST request to /api/documents with the largest allowed file size
    upload_response = request.post("/api/documents", files=file, headers={"Content-Type": "multipart/form-data"})

    # Verify the HTTP status code
    assert upload_response.status == 201

    # Verify the database state using the DBAssertionHelper
    assert db_asserter.verify_document_ingested(db_session, "largest_file.txt")

    # Cleanup: delete the uploaded file
    db_session.query(Document).filter(Document.filename == "largest_file.txt").delete()
    db_session.commit()