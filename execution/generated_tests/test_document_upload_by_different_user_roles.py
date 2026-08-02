import pytest
from playwright.sync_api import Playwright, Page, Browser
from database.assertions import db_asserter
from sqlalchemy.orm import Session
from typing import Dict

# Define a Page class using the Page Object Model (not applicable for API Backend tests)

@pytest.fixture
def db_session():
    # Initialize a DB session (e.g., using SQLAlchemy)
    # For demonstration purposes, assume this fixture is already implemented
    pass

def test_document_upload_as_admin(playwright: Playwright, db_session: Session):
    # Authenticate as admin
    browser: Browser = playwright.chromium.launch(headless=False)
    page: Page = browser.new_page()
    page.goto("http://localhost:8080/login")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin_password")
    page.click("button[type='submit']")

    # Send a POST request to /api/documents with a valid document
    with page.expect_response(lambda response: response.status == 201) as response_info:
        page.request.post("http://localhost:8080/api/documents", headers={"Content-Type": "application/json"}, data='{"filename": "document1.txt", "content": "Hello World"}')

    # Verify the document record is persisted in the database
    assert db_asserter.verify_document_ingested(db_session, "document1.txt")

    # Close the browser
    browser.close()

def test_document_upload_as_user(playwright: Playwright, db_session: Session):
    # Authenticate as user
    browser: Browser = playwright.chromium.launch(headless=False)
    page: Page = browser.new_page()
    page.goto("http://localhost:8080/login")
    page.fill("input[name='username']", "user")
    page.fill("input[name='password']", "user_password")
    page.click("button[type='submit']")

    # Send a POST request to /api/documents with a valid document
    with page.expect_response(lambda response: response.status == 201) as response_info:
        page.request.post("http://localhost:8080/api/documents", headers={"Content-Type": "application/json"}, data='{"filename": "document2.txt", "content": "Hello World"}')

    # Verify the document record is persisted in the database
    assert db_asserter.verify_document_ingested(db_session, "document2.txt")

    # Close the browser
    browser.close()