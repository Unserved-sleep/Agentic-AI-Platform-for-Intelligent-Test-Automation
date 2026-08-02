import pytest
from playwright.sync_api import request

class DocumentPage:
    def __init__(self, request):
        self.request = request

    def upload_document(self, document):
        response = self.request.post("/api/documents", data=document)
        return response

@pytest.fixture
def document_page(request):
    return DocumentPage(request)

def test_upload_without_authentication(document_page):
    # Arrange
    document = {"filename": "test_document.txt", "content": "Test content"}

    # Act
    response = document_page.upload_document(document)

    # Assert
    assert response.status == 401

def test_upload_without_authentication_api_contract(request):
    # Act
    response = request.post("/api/documents", data={"filename": "test_document.txt", "content": "Test content"})

    # Assert
    assert response.status == 401