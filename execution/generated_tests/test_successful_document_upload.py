import pytest
from playwright.sync_api import sync_playwright
from database.assertions import db_asserter
from sqlalchemy.orm import sessionmaker
from .models import Document, engine

@pytest.fixture
def db_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def request_context():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        yield context
        context.close()
        browser.close()

def test_upload_document(request_context, db_session):
    document = {"filename": "example.txt", "content": "Hello World"}
    with open("example.txt", "w") as f:
        f.write(document["content"])

    with request_context as context:
        with context.expect_request(lambda request: request.method == "POST" and request.url == "/api/documents") as request_info:
            response = context.fetch("POST", "/api/documents", {"headers": {"Content-Type": "multipart/form-data"}, "data": {"document": open("example.txt", "rb")}})

    assert response.status == 201
    assert db_asserter.verify_document_ingested(db_session, document["filename"])