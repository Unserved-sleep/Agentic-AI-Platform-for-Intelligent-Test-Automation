import pytest
from playwright.sync_api import APIRequestContext

def test_TS_005(request: APIRequestContext):
    response = request.post("/api/documents")
    expect(response.status).to_be(400)