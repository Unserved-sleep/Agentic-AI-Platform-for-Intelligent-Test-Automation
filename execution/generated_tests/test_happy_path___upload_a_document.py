import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def api_request_context(playwright):
    context = playwright.request.new_context(base_url='http://localhost:8000')
    yield context
    context.dispose()

@pytest.fixture
def db_session():
    from database.connection import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

def test_TS_001_upload_document(api_request_context: APIRequestContext, db_session):
    file_path = 'path/to/valid/example.pdf'  # replace with the actual path to a valid PDF file
    with open(file_path, 'rb') as file:
        response = api_request_context.post('/api/documents', data={'file': file})
    assert response.status == 201
    filename = file_path.split('/')[-1]
    db_asserter.verify_document_ingested(db_session, filename)