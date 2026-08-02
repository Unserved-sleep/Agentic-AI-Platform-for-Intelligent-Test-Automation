from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore

_client = None

def get_qdrant_client():
    global _client
    if _client is None:
        _client = QdrantClient(path="./backend/qdrant_data")
    return _client

def get_vector_store(collection_name: str = "insurance_knowledge") -> QdrantVectorStore:
    # Re-use the singleton client to avoid lock collisions inside the same process
    return QdrantVectorStore(client=get_qdrant_client(), collection_name=collection_name)
