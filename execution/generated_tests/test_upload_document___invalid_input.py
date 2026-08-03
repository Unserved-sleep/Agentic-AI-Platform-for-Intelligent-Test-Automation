import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # Establish a database connection
    # Replace with your actual database connection function
    def establish_database_connection():
        # Your database connection code here
        pass
    return establish_database_connection()

def test_upload_document_invalid_input(request: APIRequestContext, db_session):
    file = {"file": ("invalid_file.exe", b"executable file contents", "application/x-executable")}
    response = request.post("/api/documents", data={"file": file})
    assert response.status == 400
    assert "Invalid file type" in response.text
    assert not db_asserter.verify_document_ingested(db_session, "invalid_file.exe")