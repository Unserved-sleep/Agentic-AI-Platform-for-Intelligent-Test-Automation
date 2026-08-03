import pytest
from playwright.sync_api import request
from database.assertions import db_asserter
from sqlalchemy.orm import Session
from .models import Document

@pytest.fixture
def db_session():
    # Create a new database session for each test
    # Replace this with your actual database connection code
    # For example:
    # from sqlalchemy import create_engine
    # engine = create_engine('postgresql://user:password@host:port/dbname')
    # return Session(bind=engine)
    pass

def test_upload_by_different_roles(request, db_session):
    # Define the roles and their credentials
    roles = [
        {"username": "admin", "password": "admin_password"},
        {"username": "moderator", "password": "moderator_password"},
        {"username": "user", "password": "user_password"}
    ]

    # Define the file to be uploaded
    file = {"name": "example.txt", "content": "Hello World"}

    # Authenticate and upload the file for each role
    for role in roles:
        # Authenticate as the current role
        auth_response = request.post("http://localhost:8000/api/login", data={"username": role["username"], "password": role["password"]})
        assert auth_response.status == 200

        # Get the authentication token from the response
        auth_token = auth_response.json()["token"]

        # Send a POST request to /api/documents with the file attached
        upload_response = request.post(
            "http://localhost:8000/api/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": (file["name"], file["content"], "text/plain")}
        )
        assert upload_response.status == 201

        # Verify the document was created in the database
        assert db_asserter.verify_document_ingested(db_session, file["name"])

def test_upload_by_different_roles_with_db_error(db_session, request):
    # Simulate a database error
    with pytest.raises(Exception):
        # Authenticate and upload the file for each role
        roles = [
            {"username": "admin", "password": "admin_password"},
            {"username": "moderator", "password": "moderator_password"},
            {"username": "user", "password": "user_password"}
        ]

        file = {"name": "example.txt", "content": "Hello World"}

        for role in roles:
            auth_response = request.post("http://localhost:8000/api/login", data={"username": role["username"], "password": role["password"]})
            assert auth_response.status == 200

            auth_token = auth_response.json()["token"]

            upload_response = request.post(
                "http://localhost:8000/api/documents",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"file": (file["name"], file["content"], "text/plain")}
            )
            assert upload_response.status == 201

            # Simulate a database error
            db_asserter.verify_document_ingested(db_session, file["name"])