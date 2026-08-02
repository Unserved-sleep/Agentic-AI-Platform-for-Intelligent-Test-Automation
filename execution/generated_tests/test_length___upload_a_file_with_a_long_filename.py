import pytest
from playwright.sync_api import Playwright, APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def request_context(playwright: Playwright) -> APIRequestContext:
    return playwright.request.new_context(base_url="http://localhost:8080")

def test_upload_file_with_long_filename(request_context: APIRequestContext, db_session):
    # Generate a file with a long filename
    filename = "a" * 200 + ".txt"
    file_contents = b"Hello World!"

    # Send a POST request to /api/documents with the file attached
    with open("temp_file.txt", "wb") as f:
        f.write(file_contents)
    with open("temp_file.txt", "rb") as f:
        response = request_context.post("/api/documents", files={"file": (filename, f, "text/plain")})

    # Verify the response status code
    assert response.status == 201

    # Verify the document record persisted in the database
    assert db_asserter.verify_document_ingested(db_session, filename)

    # Remove the temporary file
    import os
    os.remove("temp_file.txt")

def test_upload_file_with_long_filename_failure(request_context: APIRequestContext):
    # Generate a file with a long filename
    filename = "a" * 200 + ".txt"
    file_contents = b"Hello World!"

    # Send a POST request to /api/documents with the file attached
    with open("temp_file.txt", "wb") as f:
        f.write(file_contents)
    with open("temp_file.txt", "rb") as f:
        response = request_context.post("/api/documents", files={"file": (filename, f, "text/plain")})

    # Verify the response status code
    assert response.status == 201

    # Remove the temporary file
    import os
    os.remove("temp_file.txt")