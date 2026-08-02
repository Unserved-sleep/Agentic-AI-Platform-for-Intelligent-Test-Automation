# Product Requirement Document (PRD)

## Project: Intelligent Test Automation Platform

### Objective
To build an AI-powered platform that automatically generates, runs, and verifies test cases for our insurance backend systems.

### Scope
- **Requirement Agent:** A system that ingests PDFs and Markdown files containing business logic (claims, underwriting) into a vector database (Qdrant) using LlamaIndex.
- **Test Generation:** An LLM reads the context (RAG) and generates API test scripts.
- **Execution & Assertion:** The platform executes the tests against the FastAPI backend and validates the responses and the underlying PostgreSQL database state.

### Key Components
1. FastAPI Backend
2. PostgreSQL Database for persistent state
3. Qdrant for vector storage (Embeddings)
4. LlamaIndex for Retrieval-Augmented Generation (RAG)

### Success Criteria
- The RAG system should accurately retrieve context related to "motor", "health", and "travel" insurance from ingested documents.
- The assertion helper must be able to read and validate the PostgreSQL database securely.
