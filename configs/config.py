"""
Configuration Settings: Centralized environment-backed settings for the platform.
Loads database, LLM API, Qdrant, and Playwright configuration from .env file
and provides Path objects for all system directories.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Sandy168$")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "agentic_test_db")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
DEFAULT_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"

# Vector Store / Qdrant settings
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_STORAGE_PATH = str(BASE_DIR / "artifacts" / "qdrant_db")

# LLM API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# UI Testing Target Website
UI_TARGET_URL = os.getenv("UI_TARGET_URL", "https://www.saucedemo.com/")

# Browser Automation & Artifact Tracing Configurations
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # Set to false to visually open browser window!
ENABLE_SCREENSHOTS = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
ENABLE_VIDEO = os.getenv("ENABLE_VIDEO", "true").lower() == "true"
CAPTURE_PASSED_TESTS = os.getenv("CAPTURE_PASSED_TESTS", "true").lower() == "true"  # Always capture for all tests

# System Directories
GENERATED_TESTS_DIR = BASE_DIR / "generated_tests"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
TRACES_DIR = ARTIFACTS_DIR / "traces"
VIDEOS_DIR = ARTIFACTS_DIR / "videos"
DOCS_DIR = BASE_DIR / "docs"

for directory in [GENERATED_TESTS_DIR, ARTIFACTS_DIR, SCREENSHOTS_DIR, TRACES_DIR, VIDEOS_DIR, ARTIFACTS_DIR / "qdrant_db", DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
