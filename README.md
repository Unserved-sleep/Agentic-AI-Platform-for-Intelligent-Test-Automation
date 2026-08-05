# Agentic AI Platform for Intelligent Test Automation

An enterprise-grade, multi-agent AI platform that automates the **end-to-end software testing lifecycle** — from ingesting requirements documents to generating, executing, and self-healing Playwright test scripts — all powered by Groq AI (Llama 3.3 70B), LangGraph, and a PostgreSQL-backed analytics dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [How It Works](#how-it-works)

---

## Overview

This platform eliminates the manual burden of writing and maintaining test suites. Feed it a Business Requirements Document (BRD), a user story, or an API spec — and it autonomously:

1. Parses and understands requirements using RAG (Retrieval-Augmented Generation) over Qdrant
2. Generates comprehensive test scenarios (positive, negative, boundary, security, API)
3. Writes executable Playwright scripts using the Page Object Model pattern
4. Runs the scripts and captures screenshots, videos, and traces
5. Diagnoses failures and self-heals broken scripts in a bounded LangGraph loop

The demo domain is an **Insurance Claims Management Portal** (`agentic_test_db`), but the platform is domain-agnostic.

---

## Architecture

```
BRD / User Story / API Spec
         │
         ▼
  ┌─────────────────┐
  │ Document Parser  │  (PDF, DOCX, TXT, MD)
  │  + RAG Pipeline  │  → Qdrant vector store
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │Requirement Agent │  Extracts structured context
  └────────┬────────┘
           │
           ▼
  ┌──────────────────────┐
  │ Test Scenario Agent   │  Positive / Negative / Boundary
  │                       │  Security / API Backend Logic
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ Playwright Script     │  POM UI scripts
  │ Agent                 │  API scripts + DBAssertionHelper
  └──────────┬───────────┘
             │
    ┌────────▼────────┐
    │  LangGraph Loop  │
    │                  │
    │  ┌───────────┐   │
    │  │  Execute  │◄──┤── Playwright runner
    │  └─────┬─────┘   │     screenshots / videos / traces
    │        │         │
    │  ┌─────▼─────┐   │
    │  │  Observe  │   │   All failures?
    │  └─────┬─────┘   │
    │        │         │
    │  ┌─────▼─────┐   │
    │  │   Repair  │   │   FailureAnalysisAgent
    │  │(Self-Heal)│   │   SelfHealingAgent
    │  └─────┬─────┘   │   → rewrites broken script
    │        └─────────┤── retry (max 2)
    └─────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │  Report Agent         │  HTML / JSON / Markdown
  │  PostgreSQL DB        │  Persisted run history
  │  Streamlit Dashboard  │  Live analytics & artifact viewer
  └──────────────────────┘
```

---

## Features

| Feature | Details |
|---|---|
| **Document Ingestion** | Ingest BRDs, user stories, API specs (PDF, DOCX, TXT, MD) into a Qdrant vector store |
| **AI Scenario Generation** | Automatically generates Positive, Negative, Boundary, Security, and API Backend Logic test scenarios via Groq LLM |
| **Playwright Script Studio** | Generates Page Object Model (POM) UI scripts and API test scripts with integrated `DBAssertionHelper` for direct PostgreSQL read-only validation |
| **LangGraph Orchestration** | 5-node state graph: `Planner → Generate → Execute → Observe → Repair` with bounded retry loop |
| **Self-Healing Engine** | Diagnoses root cause (`UI locator drift`, `API contract drift`, `backend business-logic regression`), rewrites code, and re-executes |
| **Artifact Collection** | Per-run screenshots, video recordings (`.webm`), and Playwright trace bundles (`.zip`) |
| **Full Report Pipeline** | HTML, JSON, and Markdown report generation with per-scenario pass/fail detail |
| **Streamlit Dashboard** | Live execution progress, QA analytics, execution history, artifact viewer, and downloadable HTML reports |
| **FastAPI Backend** | REST API exposing the full platform: ingestion, scenario generation, script generation, execution, and reporting |
| **PostgreSQL Persistence** | All runs, scenarios, scripts, and results are stored in `agentic_test_db` via SQLAlchemy ORM |
| **Docker Support** | One-command `docker compose up` brings up Postgres 17, Qdrant, FastAPI backend, and Streamlit dashboard |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.60 |
| Backend | FastAPI 0.141 + Uvicorn |
| Database | PostgreSQL 17 + SQLAlchemy 2.0 |
| LLM Engine | Groq API — `llama-3.3-70b-versatile` |
| Agent Framework | LangGraph 1.2 + PydanticAI 2.22 |
| Vector Store | Qdrant 1.18 (local) |
| Browser Automation | Playwright 1.42 (Python) |
| Testing | pytest 9.1 + pytest-playwright |
| Observability | Logfire |
| Language | Python 3.10 |

---

## Project Structure

```
├── agents/                    # AI agent implementations
│   ├── llm_client.py          #   Groq LLM client
│   ├── requirement_agent.py   #   Parses BRD into structured context
│   ├── test_scenario_agent.py #   Generates test scenarios via LLM
│   ├── script_agent.py        #   Generates Playwright scripts
│   ├── failure_agent.py       #   Root-cause analysis of failures
│   ├── self_healing_agent.py  #   Rewrites broken scripts
│   └── report_agent.py        #   Generates test reports
│
├── backend/
│   └── main.py                # FastAPI application + all REST endpoints
│
├── dashboard/
│   ├── app.py                 # Streamlit entry point
│   ├── pages/                 #   Home, analytics, execution history, artifact viewer, report viewer
│   ├── components/            #   Status badges, metrics cards, report table
│   └── services/              #   Report loader, artifact service
│
├── database/
│   ├── models.py              # SQLAlchemy ORM models (Claim, Payout, Document, Scenario, Script, Run)
│   ├── connection.py          # DB connection pool
│   ├── persistence.py         # CRUD helpers
│   └── assertions.py          # DBAssertionHelper — read-only SQL assertions for tests
│
├── execution/
│   ├── runner.py              # Top-level test runner entry point
│   ├── runners/               #   PlaywrightUIRunner
│   ├── browser/               #   BrowserManager, PlaywrightEngine, BrowserFactory
│   ├── collectors/            #   Screenshot, video, trace, log, artifact collectors
│   ├── services/              #   ExecutionService
│   ├── models/                #   ExecutionResult, ExecutionRequest, BrowserSession, ArtifactBundle
│   └── enums/                 #   ExecutionStatus, ExecutionType, BrowserType, ArtifactType
│
├── orchestration/
│   └── graph.py               # LangGraph state graph (5-node Planner→Generate→Execute→Observe→Repair)
│
├── ingestion/
│   └── parser.py              # Multi-format document parser (PDF, DOCX, TXT, MD)
│
├── rag/
│   ├── pipeline.py            # RAG pipeline — chunking, embedding, Qdrant upsert + retrieval
│   └── loader.py              # Document loader
│
├── reports/
│   ├── report_generator.py    # Orchestrates report generation
│   ├── models/                #   Report, ReportSection data models
│   └── generators/            #   HTML, JSON, Markdown generators
│
├── prompts/
│   └── system_prompts.py      # All LLM system prompts
│
├── shared/
│   ├── schemas.py             # Pydantic schemas shared across modules
│   └── logger.py              # Structured logging setup
│
├── configs/
│   └── config.py              # Centralised settings (env-backed via pydantic-settings)
│
├── generated_tests/           # LLM-generated Playwright test files (auto-populated)
├── artifacts/                 # Per-run screenshots, videos, traces, logs
├── docs/                      # Sample BRDs and policy documents for ingestion
├── scripts/
│   └── init_db.py             # Database initialisation + seed data
│
├── tests/                     # Platform unit & integration tests
│   ├── test_platform.py
│   ├── execution/
│   ├── reports/
│   ├── dashboard/
│   └── integration/
│
├── docker/
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── pytest.ini
└── .env.example
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL 17 running locally on port `5432`
- A [Groq API key](https://console.groq.com/) (free tier available)
- Qdrant running locally on port `6333` (or via Docker — see below)
- Playwright browsers installed

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd Agentic-AI-Platform-for-Intelligent-Test-Automation
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and set your Groq API key:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Sandy168$
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_test_db

GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 3. Initialise the database

```bash
.\venv\Scripts\python scripts/init_db.py
```

This creates the `agentic_test_db` schema and seeds sample insurance claims data.

### 4. Start the FastAPI backend

```bash
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`.

### 5. Launch the Streamlit dashboard

```bash
.\venv\Scripts\streamlit run dashboard/app.py
```

Dashboard is available at `http://localhost:8501`.

### 6. Run the test suite

```bash
.\venv\Scripts\pytest tests/ -v
```

---

## Docker Setup

Spin up the entire stack (Postgres 17, Qdrant, FastAPI backend, Streamlit dashboard) with a single command:

```bash
# Set your Groq key first
set GROQ_API_KEY=gsk_your_key_here   # Windows
# export GROQ_API_KEY=gsk_...        # Linux/macOS

docker compose up --build
```

| Service | URL |
|---|---|
| FastAPI backend | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Streamlit dashboard | http://localhost:8501 |
| Qdrant UI | http://localhost:6333/dashboard |

---

## Configuration

All settings are managed via environment variables and loaded through `configs/config.py` (pydantic-settings). The full list of available variables is in `.env.example`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Platform health check |
| `POST` | `/api/v1/ingest` | Ingest a document into Qdrant + DB |
| `POST` | `/api/v1/scenarios/generate` | Generate test scenarios from ingested requirements |
| `POST` | `/api/v1/scripts/generate` | Generate Playwright scripts for a scenario |
| `POST` | `/api/v1/execute` | Execute a test script |
| `POST` | `/api/v1/orchestrate` | Run the full LangGraph workflow |
| `POST` | `/api/v1/reports/generate` | Generate an HTML/JSON/Markdown report |
| `GET` | `/api/v1/claims` | List all insurance claims (demo domain) |
| `POST` | `/api/v1/claims` | Submit a new claim |
| `POST` | `/api/v1/claims/{id}/approve` | Approve a claim + trigger payout |
| `POST` | `/api/v1/claims/{id}/reject` | Reject a claim |
| `GET` | `/api/v1/payouts` | List all payout records |

Full interactive documentation is served at `http://localhost:8000/docs` when the backend is running.

---

## Running Tests

```bash
# All tests
.\venv\Scripts\pytest tests/ -v

# Unit tests only
.\venv\Scripts\pytest tests/execution tests/reports tests/dashboard -v

# Integration tests
.\venv\Scripts\pytest tests/integration -v

# With coverage
.\venv\Scripts\pytest tests/ --cov=. --cov-report=html
```

---

## How It Works

### 1. Document Ingestion
Upload a BRD, user story, API spec, or policy document (PDF, DOCX, TXT, or Markdown). The `DocumentParser` extracts raw text, the `RAGPipeline` chunks and embeds it into Qdrant, and the `RequirementAgent` builds a structured context object that downstream agents can query.

### 2. Scenario Generation
The `TestScenarioAgent` prompts Groq (Llama 3.3 70B) with the structured requirements and generates a rich suite of test scenarios across five categories: **Positive**, **Negative**, **Boundary**, **Security**, and **API Backend Logic**.

### 3. Script Generation
The `PlaywrightScriptAgent` converts each scenario into a runnable Python test file saved to `generated_tests/`. UI tests use the **Page Object Model** pattern. API tests use `httpx` and include `DBAssertionHelper` calls that execute read-only SQL queries directly against PostgreSQL to validate backend state (e.g., verifying a payout record was created on claim approval).

### 4. LangGraph Execution Loop
The `LoopOrchestrator` runs a 5-node LangGraph state graph:
- **Planner** — initialises state and retry budget
- **Generate** — calls scenario and script agents
- **Execute** — runs all scripts via the Playwright runner; collects screenshots, video, and traces per run
- **Observe** — checks pass/fail outcomes and decides whether to repair or end
- **Repair** — `FailureAnalysisAgent` classifies the root cause; `SelfHealingAgent` rewrites the broken script; the loop retries up to 2 times

### 5. Reporting & Dashboard
The `ReportAgent` produces HTML, JSON, and Markdown reports from execution results. All run data is persisted to PostgreSQL. The Streamlit dashboard provides live execution status, historical analytics, a per-scenario artifact viewer (screenshots, videos, traces), and downloadable reports.
