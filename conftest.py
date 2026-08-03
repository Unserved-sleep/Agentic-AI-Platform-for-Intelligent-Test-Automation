"""
Root conftest.py
================
Ensures the project root is on sys.path so that all packages
(dashboard, reports, execution, etc.) are importable in pytest
without requiring a pip install.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest
import os

@pytest.fixture
def api_request_context(playwright):
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()

@pytest.fixture
def db_session():
    from database.connection import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
