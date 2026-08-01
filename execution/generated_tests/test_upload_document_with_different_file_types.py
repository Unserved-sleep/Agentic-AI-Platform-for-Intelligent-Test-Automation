import pytest
from playwright.sync_api import sync_playwright
from database.assertions import db_asserter
from sqlalchemy.orm import Session
from typing import Dict
import requests
from pathlib import Path

# Assuming a fixture for db_session is available
@pytest.fixture
def db_session():
    # Code to setup and return a database session
    pass

class DocumentPage:
    def __init__(self, request_context):
        self.request_context = request_context

    def upload_document(self, file_path: str, file_type: str):
        url = "/api/documents"
        headers: Dict[str, str] = {
            "Content-Type": f"application/{file_type.lower()}",
        }
        with open(file_path, "rb") as file:
            response = self.request_context.post(url, headers=headers, data=file.read())
        return response

@pytest.mark.api_backend
def test_upload_document_with_different_file_types(request, db_session):
    # Assuming the files are located in the same directory as the test file
    pdf_file_path = Path(__file__).parent / "example.pdf"
    docx_file_path = Path(__file__).parent / "example.docx"

    document_page = DocumentPage(request)
    pdf_response = document_page.upload_document(str(pdf_file_path), "pdf")
    assert pdf_response.status == 201
    docx_response = document_page.upload_document(str(docx_file_path), "docx")
    assert docx_response.status == 201

    # Verify the documents are ingested into the database
    assert db_asserter.verify_document_ingested(db_session, pdf_file_path.name)
    assert db_asserter.verify_document_ingested(db_session, docx_file_path.name)