import pytest
from playwright.sync_api import request
from database.assertions import db_asserter
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection settings
DATABASE_URL = "postgresql://user:password@host:port/dbname"

# Create a database engine
engine = create_engine(DATABASE_URL)

# Create a session maker
Session = sessionmaker(bind=engine)

@pytest.fixture
def db_session():
    """Create a database session fixture"""
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_minimum_file_size_upload(request, db_session):
    # Create a file with the minimum allowed size
    file_contents = b'\x00'  # The smallest possible file
    filename = "minimum_file.txt"

    # Send a POST request to /api/documents with the minimum-sized file attached
    # in the request body as multipart/form-data
    response = request.post(
        "/api/documents",
        headers={"Content-Type": "multipart/form-data"},
        data={"file": (filename, file_contents, "text/plain")},
    )

    # Verify the request returns a 201 Created status code
    assert response.status == 201

    # Check the database for a newly created Document record with the correct filename
    assert db_asserter.verify_document_ingested(db_session, filename)

    # Cleanup: Remove the uploaded file from the database
    db_session.query(Document).filter(Document.filename == filename).delete()
    db_session.commit()