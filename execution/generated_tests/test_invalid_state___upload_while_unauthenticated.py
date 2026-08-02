import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import APIRequestContext

class PageHelper:
    @pytest.fixture
    def page(self, playwright):
        return playwright.chromium.launch(headless=True).new_page()

@pytest.mark.api_contract
def test_upload_document_unauthenticated(api_request):
    response = api_request.post("/api/documents")
    assert response.status == 401

def test_upload_document_unauthenticated_playwright(page):
    context = page.context
    request_context = context.request
    response = request_context.post("/api/documents")
    expect(response.status).to_equal(401)

@pytest.fixture
def api_request():
    with APIRequestContext() as request:
        yield request

def test_upload_document_unauthenticated_using_fixture(api_request):
    response = api_request.post("/api/documents")
    assert response.status == 401