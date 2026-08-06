# 🤖 Agentic AI Platform for Intelligent Test Automation

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-success)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Railway-blue)
![Playwright](https://img.shields.io/badge/Playwright-Automation-brightgreen)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-purple)
![Groq](https://img.shields.io/badge/Groq-Llama3.3-orange)
![Railway](https://img.shields.io/badge/Hosted%20on-Railway-black)

</p>

---

# 📌 Overview

The **Agentic AI Platform for Intelligent Test Automation** is an end-to-end AI-powered software testing platform that automatically transforms business requirement documents into executable Playwright automation suites using a collection of specialized AI agents.

The platform combines **Retrieval-Augmented Generation (RAG)**, **Large Language Models (LLMs)**, **LangGraph orchestration**, **FastAPI**, **Playwright**, **PostgreSQL**, and **Streamlit** into one intelligent testing ecosystem capable of generating, executing, repairing, and analyzing automated tests with minimal human intervention.

The platform supports the complete QA lifecycle:

- 📄 Requirement Document Parsing
- 🧠 AI-Powered Requirement Analysis
- 🔍 RAG-Based Context Retrieval
- 🧪 Automated UI & API Test Scenario Generation
- 💻 Playwright Script Generation
- 🚀 Test Execution
- 📸 Screenshot, Video & Trace Collection
- 🩹 AI Self-Healing for Failed Tests
- 🗄️ PostgreSQL Execution History
- 📊 Interactive Analytics Dashboard

---

# 🌐 Live Deployment

The application is deployed on **Railway** as two independent cloud services.

| Service | URL |
|----------|-----|
| 🖥️ Streamlit Dashboard | https://amused-healing-production-7e38.up.railway.app |
| ⚙️ FastAPI Backend | https://agentic-ai-platform-for-intelligent-test-automat-production.up.railway.app |
| 📚 Swagger API Documentation | https://agentic-ai-platform-for-intelligent-test-automat-production.up.railway.app/docs |

### Deployment Architecture

- **Frontend:** Streamlit Dashboard
- **Backend:** FastAPI REST API
- **Database:** PostgreSQL (Railway)
- **Vector Store:** Qdrant
- **LLM:** Groq (Llama 3.3 70B)
- **Hosting:** Railway

The Streamlit frontend communicates with the FastAPI backend through REST APIs while all execution history, generated artifacts, and analytics are persisted in PostgreSQL.

---

# ✨ Key Features

## 📄 Requirement Ingestion

- Upload PDF, DOCX, TXT and Markdown files
- Automatic document parsing
- Workflow extraction
- Validation extraction
- API endpoint identification

---

## 🧠 Retrieval-Augmented Generation (RAG)

- Intelligent document chunking
- Semantic vector search
- Context-aware prompt generation
- Requirement retrieval using Qdrant
- AI-enhanced document understanding

---

## 🤖 Multi-Agent AI Workflow

The platform consists of multiple specialized AI agents.

| Agent | Responsibility |
|--------|---------------|
| Requirement Agent | Requirement understanding and analysis |
| Test Scenario Agent | Generates UI & API test cases |
| Script Agent | Creates executable Playwright scripts |
| Failure Analysis Agent | Detects failure causes |
| Self-Healing Agent | Repairs broken Playwright scripts |
| Report Agent | Generates QA analytics and reports |

---

## 🧪 Intelligent Test Generation

Automatically generates:

- UI Test Cases
- API Test Cases
- Positive Test Cases
- Negative Test Cases
- Boundary Tests
- Database Assertion Tests

---

## 💻 Playwright Automation

Supports:

- Python Playwright Framework
- Page Object Model
- Browser Automation
- REST API Testing
- Screenshots
- Video Recording
- Playwright Traces
- Execution Logs

---

## 🩹 AI Self-Healing Engine

Instead of only reporting failures, the platform attempts automatic recovery.

Capabilities include:

- Broken locator detection
- XPath repair
- CSS selector repair
- Retry execution
- AI patch explanation
- Healing audit logs

---

## 📊 Interactive Dashboard

The Streamlit dashboard includes:

- Dashboard Overview
- Requirement Ingestion
- RAG Pipeline
- Test Scenario Generator
- Script Studio
- Execution Console
- Artifact Viewer
- Self-Healing Console
- PostgreSQL Inspector
- Analytics Dashboard
- Demo Database Reset

---

## 🗄️ PostgreSQL Persistence

Automatically stores:

- Documents
- Test Scenarios
- Generated Scripts
- Execution History
- Healing Logs
- Database Assertions

Automatic database features:

- Database creation
- Schema creation
- Table migration
- Seed data generation

---

## 📸 Generated Artifacts

Every execution can generate:

- 📸 Screenshots
- 🎥 Browser Videos
- 🔍 Playwright Traces
- 📄 Console Logs
- 📊 Execution Reports
- 🗄️ Database Assertion Reports

---

# 🏗️ High-Level Architecture

```text
Business Requirement Document
            │
            ▼
     Document Parser
            │
            ▼
   Requirement Agent
            │
            ▼
      RAG Pipeline
     (Qdrant Vector DB)
            │
            ▼
 Test Scenario Generator
            │
            ▼
 Playwright Script Agent
            │
            ▼
     Execution Engine
            │
 ┌──────────┼──────────┐
 ▼          ▼          ▼
UI Tests  API Tests  DB Assertions
            │
            ▼
 Self-Healing Engine
            │
            ▼
 PostgreSQL Persistence
            │
            ▼
 Streamlit Analytics Dashboard
```

---

# ☁️ Deployment Architecture

```text
                    Railway Cloud

        ┌───────────────────────────────┐
        │                               │
        │     Streamlit Dashboard       │
        │              │                │
        │              ▼                │
        │      FastAPI Backend          │
        │              │                │
        │              ▼                │
        │   PostgreSQL Database         │
        │                               │
        └───────────────────────────────┘
                    ▲
                    │
               Groq LLM API

                    ▲
                    │
              Qdrant Vector DB
```

---

# 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| Programming Language | Python 3.10+ |
| Frontend | Streamlit |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Automation | Playwright |
| AI Framework | LangGraph |
| LLM | Groq (Llama 3.3 70B) |
| Vector Store | Qdrant |
| Document Processing | PyPDF2, python-docx |
| Data Processing | Pandas |
| HTTP Client | Requests, HTTPX |
| Deployment | Railway |

---

# 📁 Project Structure

```text
Agentic-AI-Platform/
│
├── agents/
│   ├── requirement_agent.py
│   ├── test_scenario_agent.py
│   ├── script_agent.py
│   ├── failure_agent.py
│   ├── self_healing_agent.py
│   └── report_agent.py
│
├── dashboard/
│   └── app.py
│
├── database/
│   ├── connection.py
│   ├── models.py
│   ├── persistence.py
│   └── assertions.py
│
├── execution/
│   └── runner.py
│
├── ingestion/
├── rag/
├── orchestration/
├── configs/
├── docs/
├── generated_tests/
├── artifacts/
│   ├── screenshots/
│   ├── traces/
│   ├── videos/
│   └── qdrant_db/
│
├── main.py
├── requirements.txt
└── README.md
```

---
# 🚀 Installation & Setup

## Prerequisites

Before running the project, ensure the following are installed:

- Python 3.10+
- PostgreSQL 17+
- Git
- Playwright
- Groq API Key
- Qdrant

---

## Clone Repository

```bash
git clone https://github.com/<your-username>/Agentic-AI-Platform-for-Intelligent-Test-Automation.git

cd Agentic-AI-Platform-for-Intelligent-Test-Automation
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Playwright Browsers

```bash
playwright install
```

---

# ⚙️ Environment Variables

Create a `.env` file in the project root.

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_test_db

# Database URL
DATABASE_URL=postgresql://postgres:password@localhost:5432/agentic_test_db

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Backend URL (for Streamlit)
BACKEND_URL=http://localhost:8000
```

---

# 🗄️ Database Initialization

The application automatically:

- Creates PostgreSQL database
- Creates tables
- Performs schema migration
- Seeds sample claims & payouts

No manual SQL execution is required.

---

# ▶️ Running the Project Locally

## Step 1 – Start FastAPI Backend

```bash
uvicorn main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

Swagger Documentation:

```
http://localhost:8000/docs
```

---

## Step 2 – Start Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard runs at:

```
http://localhost:8501
```

---

# ☁️ Railway Deployment

The project is deployed as **two independent Railway services**.

## 🖥️ Streamlit Dashboard

https://amused-healing-production-7e38.up.railway.app

Responsible for:

- Dashboard UI
- Requirement Upload
- AI Scenario Generation
- Script Viewer
- Test Execution
- Analytics
- Self-Healing Console

---

## ⚙️ FastAPI Backend

https://agentic-ai-platform-for-intelligent-test-automat-production.up.railway.app

Responsible for:

- REST APIs
- AI Agent Orchestration
- RAG Pipeline
- PostgreSQL Operations
- Test Execution
- Database Assertions

---

## 📚 Swagger API Documentation

https://agentic-ai-platform-for-intelligent-test-automat-production.up.railway.app/docs

---

# 📡 API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Health Check |
| GET | /docs | Swagger Documentation |
| POST | /ingest | Upload Requirement Document |
| POST | /generate-scenarios | Generate Test Scenarios |
| POST | /generate-script | Generate Playwright Scripts |
| POST | /execute | Execute Generated Tests |
| POST | /heal | Trigger Self-Healing |
| GET | /report | Generate Analytics Report |

> **Note:** Endpoint names may vary depending on your implementation.

---

# 📊 Streamlit Dashboard Modules

The dashboard consists of six major modules:

### 📊 Dashboard Overview

- Live Service Status
- PostgreSQL Metrics
- Database Verification
- Execution Statistics

---

### 📄 Requirement Ingestion & RAG

- Upload BRDs
- Parse Documents
- Build RAG Context
- Requirement Analysis

---

### 🧪 Test Scenario Generator

- Generate UI Tests
- Generate API Tests
- Positive/Negative Scenarios
- Database Assertions

---

### 💻 Playwright Script Studio

- Generate Python Scripts
- Page Object Models
- Script Preview
- API Test Scripts

---

### 🚀 Execution & Self-Healing

- Execute Test Suite
- Screenshot Viewer
- Trace Download
- Video Playback
- Self-Healing
- Retry Failed Tests

---

### 📈 Analytics & Reports

- Pass Rate
- Execution History
- Healing Logs
- Database Inspector
- AI Recommendations

---

# 📸 Screenshots

Add screenshots here for better project presentation.

```
README Images/

dashboard.png

requirement_ingestion.png

scenario_generation.png

script_studio.png

execution.png

analytics.png
```

Example:

```markdown
## Dashboard

![Dashboard](images/dashboard.png)
```

---

# 🔮 Future Enhancements

- Docker Containerization
- Kubernetes Deployment
- Jenkins CI/CD Pipeline
- GitHub Actions Integration
- Azure DevOps Support
- Jira Integration
- Parallel Playwright Execution
- Multi-Browser Testing
- Email Notifications
- Slack Integration
- AI Flaky Test Detection
- Test Data Generation using LLMs

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push branch

```bash
git push origin feature/my-feature
```

5. Open a Pull Request

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Aditya Kumar**

B.Tech Computer Science Student  
SRM Institute of Science and Technology

GitHub: https://github.com/<your-github>

LinkedIn: https://linkedin.com/in/<your-linkedin>

---

# ⭐ Support

If you found this project useful:

⭐ Star this repository

🍴 Fork the repository

🛠️ Contribute to the project

📢 Share it with others

---

## Thank You!

Built with ❤️ using **FastAPI, Streamlit, PostgreSQL, Playwright, LangGraph, Groq AI, and Railway**.
