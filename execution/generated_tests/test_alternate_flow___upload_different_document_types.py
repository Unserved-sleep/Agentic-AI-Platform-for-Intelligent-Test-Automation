import pytest
from playwright.sync_api import Page, expect
from pytest_playwright import api_request

@pytest.mark.api_contract
def test_upload_different_document_types(api_request):
    # Define the document files to upload
    documents = [
        {"filename": "example.pdf", "content_type": "application/pdf"},
        {"filename": "example.docx", "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        {"filename": "example.jpg", "content_type": "image/jpeg"},
    ]

    # Upload each document and verify the response
    for document in documents:
        with api_request.context() as request:
            response = request.post("/api/documents", files={"file": (document["filename"], open(document["filename"], "rb"), document["content_type"])})
            expect(response.status).to_equal(201)

        # Additional verification can be added here if needed
```

However, to follow the problem description more closely and address potential issues like handling the request fixture correctly for API contract tests and including a clear structure for handling different document uploads and corresponding assertions, consider the following revised version:

```python
import pytest
from pytest_playwright import api_request

@pytest.mark.api_contract
def test_upload_different_document_types(api_request):
    # Define the document files to upload
    documents = [
        {"filename": "example.pdf", "content_type": "application/pdf"},
        {"filename": "example.docx", "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        {"filename": "example.jpg", "content_type": "image/jpeg"},
    ]

    for document in documents:
        with api_request.context() as request:
            with request.post("/api/documents", files={"file": (document["filename"], open(document["filename"], "rb"), document["content_type"])}) as response:
                assert response.status == 201
                assert response.headers["content-type"] == "application/json"
                # Additional verification of the response content can be added here

                # For a more robust test, verify the response body
                response_json = response.json()
                assert "filename" in response_json
                assert response_json["filename"] == document["filename"]

                # Verify any other expected fields in the response body