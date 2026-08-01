import pytest
from playwright.sync_api import Page, request
from database.assertions import db_asserter

@pytest.fixture
def page():
    return Page()

@pytest.fixture
def db_session():
    # Replace this with your actual database session setup
    # For demonstration purposes, we assume a SQLite database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('sqlite:///example.db')
    Session = sessionmaker(bind=engine)
    return Session()

def test_upload_different_file_types(page, db_session):
    # Send a POST request to /api/documents with a PDF attached
    pdf_file = {'file': ('example.pdf', open('example.pdf', 'rb'), 'application/pdf')}
    response = page.request.post('/api/documents', files=pdf_file)
    expect(response.status).to_equal(201)
    assert db_asserter.verify_document_ingested(db_session, 'example.pdf')

    # Send a POST request to /api/documents with a DOCX attached
    docx_file = {'file': ('example.docx', open('example.docx', 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    response = page.request.post('/api/documents', files=docx_file)
    expect(response.status).to_equal(201)
    assert db_asserter.verify_document_ingested(db_session, 'example.docx')

def test_upload_different_file_types_api_request(db_session):
    # Send a POST request to /api/documents with a PDF attached
    pdf_file = {'file': ('example.pdf', open('example.pdf', 'rb'), 'application/pdf')}
    with request.new_context() as new_context:
        response = new_context.post('/api/documents', files=pdf_file)
    expect(response.status).to_equal(201)
    assert db_asserter.verify_document_ingested(db_session, 'example.pdf')

    # Send a POST request to /api/documents with a DOCX attached
    docx_file = {'file': ('example.docx', open('example.docx', 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    response = new_context.post('/api/documents', files=docx_file)
    expect(response.status).to_equal(201)
    assert db_asserter.verify_document_ingested(db_session, 'example.docx')