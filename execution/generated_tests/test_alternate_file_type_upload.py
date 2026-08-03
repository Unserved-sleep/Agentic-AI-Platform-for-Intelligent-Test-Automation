import pytest
from playwright.sync_api import sync_playwright
from database.assertions import db_asserter
from your_app import db_session  # assuming db_session is a fixture or can be instantiated

@pytest.fixture
def request_context():
    with sync_playwright() as p:
        yield p.request

@pytest.mark.api_backend
def test_alternate_file_type_upload(request_context, db_session):
    # Define file types and corresponding files
    file_types = {
        "PDF": "example.pdf",
        "DOCX": "example.docx",
        "JPEG": "example.jpeg"
    }

    # Send POST request to /api/documents for each file type
    for file_type, filename in file_types.items():
        with request_context.post("/api/documents", files={"file": (filename, open(filename, "rb"), f"application/{file_type.lower()}")}) as response:
            # Verify request returns a 201 Created status code
            assert response.status == 201

            # Check database for newly created Document record
            assert db_asserter.verify_document_ingested(db_session, filename)

def test_alternate_file_type_upload_db_cleanup(db_session):
    # Cleanup database after test
    db_session.query(Document).delete()
    db_session.commit()