import pytest
from playwright.sync_api import APIRequestContext
from database.assertions import db_asserter

@pytest.fixture
def db_session():
    # Implement database session setup and teardown logic here
    # For example:
    # from sqlalchemy.orm import sessionmaker
    # from sqlalchemy import create_engine
    # engine = create_engine('postgresql://user:password@host:port/dbname')
    # Session = sessionmaker(bind=engine)
    # session = Session()
    # try:
    #     yield session
    # finally:
    #     session.close()
    pass

def test_alternate_file_type_upload(db_session: Session, request: APIRequestContext):
    file_types = [
        {"name": "example.pdf", "mime_type": "application/pdf", "path": "./example.pdf"},
        {"name": "example.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "path": "./example.docx"},
        {"name": "example.jpeg", "mime_type": "image/jpeg", "path": "./example.jpeg"},
    ]

    for file_type in file_types:
        with open(file_type["path"], "rb") as file:
            response = request.post("/api/documents",
                headers={"Content-Type": "multipart/form-data"},
                data={"file": (file_type["name"], file, file_type["mime_type"])})
            assert response.status == 201
            assert db_asserter.verify_document_ingested(db_session, file_type["name"])