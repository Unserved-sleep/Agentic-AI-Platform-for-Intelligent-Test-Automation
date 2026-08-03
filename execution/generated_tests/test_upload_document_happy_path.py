import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

def test_TS_001(db_session, request: APIRequestContext):
    file = {'file': ('example.pdf', 'example content', 'application/pdf')}
    response = request.post('/api/documents', files=file)
    assert response.status == 201
    db_asserter.verify_document_ingested(db_session, 'example.pdf')