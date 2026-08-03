import pytest
from sqlalchemy.orm import Session
from database.assertions import db_asserter
from playwright.sync_api import APIRequestContext
from pytest import fixture

@pytest.fixture
def db_session():
    # Create a database session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('postgresql://user:password@host:port/dbname')
    Session = sessionmaker(bind=engine)
    return Session()

def test_upload_document(db_session: Session, request: APIRequestContext):
    # Send a POST request to /api/documents with a valid document attached as multipart/form-data
    file_path = 'path_to_your_file.txt'
    with open(file_path, 'rb') as file:
        response = request.post('/api/documents', 
                                headers={'Content-Type': 'multipart/form-data'}, 
                                data={'file': file})
        
    # Verify the request is processed successfully
    assert response.status == 201
    
    # Verify a Document record is persisted in the database
    filename = file_path.split('/')[-1]
    assert db_asserter.verify_document_ingested(db_session, filename)