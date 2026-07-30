from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .connection import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String) # pdf, md
    domain_category = Column(String) # motor, health, travel
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class Assertion(Base):
    __tablename__ = "assertions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, index=True)
    assertion_type = Column(String) # e.g., 'db_state', 'api_response'
    passed = Column(Boolean, default=False)
    details = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
