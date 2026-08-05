"""
RAG (Retrieval-Augmented Generation) package for semantic search.

Provides document chunking, embedding generation, and Qdrant vector
store integration for context-aware LLM queries.

Key components:
- TextChunker: Splits documents into semantic chunks
- RAGPipeline: Orchestrates embedding, upsert, and retrieval

Used by RequirementAgent to extract relevant context from ingested
business requirements documents.
"""

from rag.loader import TextChunker
from rag.pipeline import RAGPipeline

__all__ = ["TextChunker", "RAGPipeline"]
