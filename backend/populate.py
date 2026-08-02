import os
import requests
import time

docs_dir = "../docs"
api_url = "http://127.0.0.1:8000"

print("Starting automated ingestion of documents...")

for filename in os.listdir(docs_dir):
    if filename.endswith(".md") or filename.endswith(".pdf"):
        filepath = os.path.join(docs_dir, filename)
        
        # 1. Upload
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "text/markdown" if filename.endswith(".md") else "application/pdf")}
            res = requests.post(f"{api_url}/upload", files=files)
            print(f"Upload {filename}:", res.json())
            
        # 2. Ingest
        domain = "general"
        if "motor" in filename.lower() or "car" in filename.lower(): domain = "motor"
        elif "health" in filename.lower(): domain = "health"
        elif "travel" in filename.lower(): domain = "travel"
        
        data = {
            "filename": filename,
            "file_type": "md" if filename.endswith(".md") else "pdf",
            "domain_category": domain
        }
        res = requests.post(f"{api_url}/ingest", json=data)
        print(f"Ingest {filename}:", res.json())

print("All documents successfully ingested into the persistent vector database!")
