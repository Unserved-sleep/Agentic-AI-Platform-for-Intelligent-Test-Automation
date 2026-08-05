"""
Database package for PostgreSQL persistence and assertions.

Provides SQLAlchemy ORM models, connection management, and helper classes
for database operations including read-only test assertions.

Key components:
- Connection management (engine, session factory)
- ORM models (Claim, Payout, Document, Scenario, Script, Execution, HealingLog)
- DBAssertionHelper for test-time database state validation
- DBPersistenceHelper for CRUD operations
"""

from database.connection import get_db, engine, Base, ensure_database_exists
from database.models import Claim, Payout, DocumentModel, ScenarioModel, ScriptModel, ExecutionModel, HealingLogModel
from database.assertions import DBAssertionHelper
from database.persistence import DBPersistenceHelper

__all__ = [
    "get_db",
    "engine",
    "Base",
    "ensure_database_exists",
    "Claim",
    "Payout",
    "DocumentModel",
    "ScenarioModel",
    "ScriptModel",
    "ExecutionModel",
    "HealingLogModel",
    "DBAssertionHelper",
    "DBPersistenceHelper"
]
