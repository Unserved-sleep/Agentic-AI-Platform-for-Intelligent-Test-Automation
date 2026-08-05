"""
Ingestion package for document parsing and text extraction.

Supports multiple document formats:
- PDF files (via PyMuPDF)
- DOCX files (via python-docx)
- Plain text files (.txt)
- Markdown files (.md)

The DocumentParser extracts structured content including workflows,
validations, and API endpoints from business requirements documents.
"""

from ingestion.parser import DocumentParser

__all__ = ["DocumentParser"]
