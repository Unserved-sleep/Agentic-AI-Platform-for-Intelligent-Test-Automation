import pytest
from playwright.sync_api import Page, expect
from database.assertions import db_asserter

@pytest.fixture
def page():
    # Assuming this fixture is provided by pytest-playwright
    pass

@pytest.fixture
def db_session():
    # Assuming this fixture is implemented to return a valid Session object
    pass

def test_upload_small_file(page: Page, db_session):
    # Define the API endpoint and the small file path
    api_endpoint = "/api/documents"
    small_file_path = "path_to_your_small_file.txt"  # Replace with the actual file path
    filename = "small_file.txt"  # Replace with the actual filename

    # Send a POST request to the API endpoint with the small file attached
    with page.context.new_page() as new_page:
        with new_page.request.post(api_endpoint, headers={"Content-Type": "multipart/form-data"}) as request:
            request.set_body({"file": (filename, open(small_file_path, "rb"), "application/octet-stream")})
            response = request.send()

    # Verify the HTTP status code
    assert response.status == 201

    # Verify the document record persisted in the database
    assert db_asserter.verify_document_ingested(db_session, filename)

def test_upload_small_file_api(page, db_session, request):
    # Alternatively, use the request fixture from pytest-playwright
    api_endpoint = "/api/documents"
    small_file_path = "path_to_your_small_file.txt"  # Replace with the actual file path
    filename = "small_file.txt"  # Replace with the actual filename

    # Send a POST request to the API endpoint with the small file attached
    response = request.post(api_endpoint, headers={"Content-Type": "multipart/form-data"}, data={"file": (filename, open(small_file_path, "rb"), "application/octet-stream")})

    # Verify the HTTP status code
    assert response.status == 201

    # Verify the document record persisted in the database
    assert db_asserter.verify_document_ingested(db_session, filename)