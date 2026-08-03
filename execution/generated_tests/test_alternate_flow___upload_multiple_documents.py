import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def api_request_context():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        context = p.request.new_context(base_url='http://localhost:8000')
        yield context
        context.dispose()

@pytest.fixture
def db_session():
    from database.connection import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

def test_ts002_upload_multiple_documents(api_request_context: APIRequestContext, db_session):
    filenames = ['example1.pdf', 'example2.pdf', 'example3.pdf']
    files = {'file': [f'file_{i}.pdf' for i in range(len(filenames))]}
    response = api_request_context.post('/api/documents', data={'filenames': filenames}, files=files)
    assert response.status == 201
    for filename in filenames:
        db_asserter.verify_document_ingested(db_session, filename)