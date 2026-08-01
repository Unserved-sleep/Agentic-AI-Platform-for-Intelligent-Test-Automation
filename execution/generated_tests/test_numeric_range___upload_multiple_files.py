import pytest
from playwright.sync_api import request
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # instantiate or inject a database session
    # for demonstration purposes, assume a simple in-memory db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    return Session()

def test_upload_multiple_files(request, db_session):
    # send a POST request to /api/documents with multiple files attached
    files = [
        {'name': 'file1.txt', 'mimeType': 'text/plain', 'buffer': b'Hello, World!'},
        {'name': 'file2.txt', 'mimeType': 'text/plain', 'buffer': b'Hello, Playwright!'}
    ]
    response = request.post("/api/documents", data={'files': files})

    # verify 201 Created status code
    assert response.status == 201

    # verify multiple document records persisted in the database
    assert db_asserter.verify_document_ingested(db_session, files[0]['name'])
    assert db_asserter.verify_document_ingested(db_session, files[1]['name'])