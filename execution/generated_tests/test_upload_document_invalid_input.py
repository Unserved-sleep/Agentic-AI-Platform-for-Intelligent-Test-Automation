import pytest
from playwright.sync_api import APIRequestContext

def test_TS_004_invalid_file_type(request: APIRequestContext):
    with request.post("/api/documents",
                       files={"file": ("invalid_file.pdf", b"Invalid file content", "application/octet-stream")}) as response:
        expect(response.status).to_equal(400)