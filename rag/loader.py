"""
Text Chunker: Splits documents into overlapping chunks for RAG embedding.
Used by the RAG pipeline to break large documents into manageable segments
before generating vector embeddings for Qdrant storage.
"""
from typing import List

class TextChunker:
    """Splits raw text documents into manageable chunks with overlap."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        if not words:
            return []

        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i : i + chunk_size]
            chunks.append(" ".join(chunk_words))
            i += (chunk_size - overlap)
        return chunks
