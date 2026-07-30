from sqlalchemy.orm import Session
from .models import Document

class DBAssertionHelper:
    """
    Read-only DB assertion helper (built on the schema/models) that will allow 
    API test scripts to verify the backend database state.
    """
    def verify_document_ingested(self, db: Session, filename: str) -> bool:
        doc = db.query(Document).filter(Document.filename == filename).first()
        return doc is not None

db_asserter = DBAssertionHelper()
