from typing import List, Dict, Any
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from configs.config import QDRANT_STORAGE_PATH, QDRANT_HOST, QDRANT_PORT
from rag.loader import TextChunker
from shared.logger import get_logger

logger = get_logger("rag.pipeline")

try:
    from fastembed import TextEmbedding
    _EMBEDDING_MODEL = TextEmbedding("BAAI/bge-small-en-v1.5")
    VECTOR_SIZE = 384
except Exception as e:
    logger.warning(f"FastEmbed model loading note: {e}")
    _EMBEDDING_MODEL = None
    VECTOR_SIZE = 384

class RAGPipeline:
    """Qdrant Vector Database RAG Pipeline for requirement context storage & retrieval."""

    def __init__(self, collection_name: str = "requirements"):
        self.collection_name = collection_name
        self.indexed_chunks: List[Dict[str, Any]] = []
        self.current_doc_id: str = ""
        try:
            # Use embedded Qdrant local storage
            self.client = QdrantClient(path=QDRANT_STORAGE_PATH)
            logger.info(f"Initialized Qdrant client at {QDRANT_STORAGE_PATH}")
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant, using local memory index: {e}")
            self.client = None

    def _ensure_collection(self):
        if not self.client:
            return
        try:
            collections = self.client.get_collections().collections
            col_names = [c.name for c in collections]
            if self.collection_name not in col_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}'.")
        except Exception as e:
            logger.warning(f"Error ensuring Qdrant collection '{self.collection_name}': {e}")

    def _embed_text(self, text: str) -> List[float]:
        if _EMBEDDING_MODEL:
            try:
                embeddings = list(_EMBEDDING_MODEL.embed([text]))
                return embeddings[0].tolist()
            except Exception as e:
                logger.warning(f"FastEmbed encoding error: {e}")

        # Fallback 384-dim dense float vector
        words = text.lower().split()
        vec = np.zeros(VECTOR_SIZE, dtype=np.float32)
        for w in words:
            h = hash(w) % VECTOR_SIZE
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def clear(self):
        """Clears existing indexed chunks to prevent cross-document contamination."""
        self.indexed_chunks = []
        self.current_doc_id = ""
        if self.client:
            try:
                self.client.delete_collection(collection_name=self.collection_name)
                logger.info(f"Deleted Qdrant collection '{self.collection_name}'.")
            except Exception as e:
                logger.debug(f"Could not delete Qdrant collection: {e}")
            self._ensure_collection()
        logger.info("Cleared RAG pipeline vector store and chunk memory.")

    def ingest_document(self, doc_id: str, text: str, replace_existing: bool = True):
        if replace_existing:
            self.clear()

        self.current_doc_id = doc_id
        chunks = TextChunker.chunk_text(text, chunk_size=300, overlap=30)
        print(f"[DEBUG RAG] Current document: {doc_id}")
        print(f"[DEBUG RAG] Ingestion source: {doc_id}")
        print(f"[DEBUG RAG] Number of chunks: {len(chunks)}")

        points = []
        for idx, chunk in enumerate(chunks):
            chunk_data = {
                "id": f"{doc_id}_{idx}",
                "doc_id": doc_id,
                "source": doc_id,
                "document_id": doc_id,
                "chunk_index": idx,
                "text": chunk
            }
            self.indexed_chunks.append(chunk_data)

            if self.client:
                vec = self._embed_text(chunk)
                points.append(
                    qmodels.PointStruct(
                        id=idx + 1,
                        vector=vec,
                        payload=chunk_data
                    )
                )

        if self.client and points:
            try:
                self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info(f"Successfully upserted {len(points)} vector points into Qdrant collection '{self.collection_name}'.")
            except Exception as e:
                logger.error(f"Failed to upsert points into Qdrant: {e}")

        logger.info(f"Ingested document '{doc_id}' into RAG pipeline ({len(chunks)} chunks).")

    def retrieve_context(self, query: str, top_k: int = 5, doc_id: str = None) -> str:
        """Retrieve relevant requirement context for the current document from Qdrant vector database."""
        target_doc_id = doc_id or self.current_doc_id

        # Try Qdrant vector retrieval first
        if self.client:
            try:
                query_vec = self._embed_text(query)
                query_filter = None
                if target_doc_id:
                    query_filter = qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="doc_id",
                                match=qmodels.MatchValue(value=target_doc_id)
                            )
                        ]
                    )

                if hasattr(self.client, "query_points"):
                    res = self.client.query_points(
                        collection_name=self.collection_name,
                        query=query_vec,
                        query_filter=query_filter,
                        limit=top_k
                    )
                    search_res = res.points if hasattr(res, "points") else res
                elif hasattr(self.client, "search"):
                    search_res = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vec,
                        query_filter=query_filter,
                        limit=top_k
                    )
                else:
                    search_res = []

                if search_res:
                    retrieved_sources = [hit.payload.get("source") for hit in search_res if getattr(hit, "payload", None)]
                    print(f"[DEBUG RAG Qdrant] Retrieved chunk sources from Qdrant: {retrieved_sources}")
                    top_chunks = [hit.payload.get("text", "") for hit in search_res if getattr(hit, "payload", None)]
                    return "\n\n--- CONTEXT CHUNK (QDRANT VECTOR DB) ---\n".join(top_chunks)
            except Exception as e:
                logger.warning(f"Qdrant vector search failed, falling back to memory index: {e}")

        # In-memory fallback
        chunks_to_search = self.indexed_chunks
        if target_doc_id:
            chunks_to_search = [c for c in self.indexed_chunks if c.get("doc_id") == target_doc_id or c.get("source") == target_doc_id]

        if not chunks_to_search:
            print(f"[DEBUG RAG] No chunks available to search for query: '{query}' (doc_id: {target_doc_id})")
            return ""

        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in chunks_to_search:
            text_words = set(chunk["text"].lower().split())
            overlap_score = len(query_words.intersection(text_words))
            scored_chunks.append((overlap_score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_entries = [c[1] for c in scored_chunks[:top_k]]
        
        retrieved_sources = [doc.get("source") for doc in top_entries]
        print(f"[DEBUG RAG Memory] Retrieved chunk sources: {retrieved_sources}")

        top_chunks = [c["text"] for c in top_entries]
        return "\n\n--- CONTEXT CHUNK ---\n".join(top_chunks)

