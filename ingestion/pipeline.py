from llama_index.core import VectorStoreIndex, StorageContext
from rag.vectorstore import get_vector_store
from rag.loader import load_document

class IngestionPipeline:
    def __init__(self):
        self.vector_store = None
        self.storage_context = None
        self.index = None

    def load_index(self):
        if not self.vector_store:
            self.vector_store = get_vector_store()
            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        if not self.index:
            try:
                self.index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
            except Exception:
                pass

    def process_file(self, file_path: str) -> int:
        documents = load_document(file_path)
        self.load_index()
        
        if self.index is None:
            self.index = VectorStoreIndex.from_documents(
                documents, 
                storage_context=self.storage_context
            )
        else:
            for doc in documents:
                self.index.insert(doc)
        return len(documents)

ingestion_pipeline = IngestionPipeline()
