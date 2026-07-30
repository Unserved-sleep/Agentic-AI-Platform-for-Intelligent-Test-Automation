from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import shutil

# Cross-module imports for the new architecture
from database.connection import engine, get_db, Base
from database.models import Document
from ingestion.pipeline import ingestion_pipeline
from rag.retriever import rag_retriever
from rag.embeddings import setup_embeddings
from rag.splitter import setup_splitter

# Initialize RAG configurations globally
setup_embeddings()
setup_splitter()

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intelligent Test Automation API")

class DocumentCreate(BaseModel):
    filename: str
    file_type: str
    domain_category: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Intelligent Test Automation Platform"}

@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "File uploaded successfully", "filename": file.filename}

@app.post("/ingest", response_model=dict)
def ingest_document(doc: DocumentCreate, db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, doc.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in uploads directory. Please upload first.")
        
    try:
        # Ingest into Qdrant via the ingestion pipeline
        num_docs = ingestion_pipeline.process_file(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    # Create DB record
    db_doc = Document(**doc.dict())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    return {
        "message": f"Document {db_doc.filename} ingested successfully.", 
        "id": db_doc.id,
        "chunks_processed": num_docs
    }

@app.get("/documents/")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()

class QueryRequest(BaseModel):
    query: str
    domain_filters: list = []

@app.post("/query")
def retrieve_context(request: QueryRequest):
    try:
        context = rag_retriever.retrieve_context(request.query, request.domain_filters)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
