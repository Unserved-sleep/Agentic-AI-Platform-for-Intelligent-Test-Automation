# Agentic AI Platform for Intelligent Test Automation

An enterprise-grade, multi-agent AI platform that automates the end-to-end software testing lifecycle using Playwright, Groq AI (Llama 3.3 70B), LangGraph, PostgreSQL, and Streamlit.

## 🚀 Features

- **Document Ingestion & Context Engineering**: Ingest BRDs, User Stories, and API specs (PDF, DOCX, TXT, MD) into Qdrant vector store.
- **AI Test Scenario Generator**: Automatically generates Positive, Negative, Boundary, Security, and API Backend Logic scenarios.
- **Playwright Script Studio**: Generates Page Object Model (POM) UI scripts and Playwright API scripts with direct PostgreSQL read-only `DBAssertionHelper` queries.
- **Loop Engineering & Self-Healing**: Bounded execution-reflection-repair cycle in LangGraph. Automatically diagnoses root cause (`UI locator drift`, `API contract drift`, `backend business-logic regression`), repairs code, and re-executes tests.
- **Interactive Streamlit Dashboard**: Full QA analytics, execution logs, live progress, and HTML report downloads.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL 17 + SQLAlchemy ORM (`agentic_test_db`)
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **Agent Framework**: LangGraph + PydanticAI
- **Automation**: Playwright (Python) + Playwright MCP

## 🚦 Quick Start

### 1. Database Setup
Ensure PostgreSQL is running locally on port 5432 with password `Sandy168$`.
Initialize database and seed sample insurance claim data:
```bash
.\venv\Scripts\python scripts/init_db.py
```

### 2. Start FastAPI Backend Server
```bash
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

### 3. Launch Streamlit Dashboard
```bash
.\venv\Scripts\streamlit run dashboard/app.py
```

### 4. Run Automated Test Suite
```bash
.\venv\Scripts\pytest tests/ -v
```
