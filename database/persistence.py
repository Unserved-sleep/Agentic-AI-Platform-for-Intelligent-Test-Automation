"""
Database Persistence Helper: CRUD operations for all platform entities.
Saves and retrieves documents, test scenarios, generated scripts, execution records,
and healing logs from PostgreSQL for full audit trail and analytics.
"""
from typing import List, Optional, Dict, Any
from database.connection import SessionLocal
from database.models import DocumentModel, ScenarioModel, ScriptModel, ExecutionModel, HealingLogModel
from shared.schemas import TestScenario, GeneratedTestScript, ExecutionResult
from shared.logger import get_logger

logger = get_logger("database.persistence")

class DBPersistenceHelper:
    """
    PostgreSQL Persistence Helper.
    Handles saving and updating documents, test scenarios, scripts, execution records,
    and healing logs in PostgreSQL.
    """

    @staticmethod
    def save_document(filename: str, title: str, raw_text: str, summary: Optional[str] = None) -> Optional[DocumentModel]:
        """Save an ingested document into PostgreSQL."""
        db = SessionLocal()
        try:
            doc = DocumentModel(
                filename=filename,
                title=title,
                raw_text=raw_text,
                summary=summary or ""
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            logger.info(f"Saved document '{filename}' (ID: {doc.id}) to PostgreSQL.")
            return doc
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving document '{filename}' to PostgreSQL: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def save_scenarios(scenarios: List[TestScenario]):
        """Save or update test scenarios in PostgreSQL."""
        if not scenarios:
            return
        db = SessionLocal()
        try:
            for sc in scenarios:
                existing = db.query(ScenarioModel).filter(ScenarioModel.id == sc.id).first()
                if existing:
                    existing.title = sc.title
                    existing.description = sc.description
                    existing.category = sc.category
                    existing.test_type = sc.test_type
                    existing.preconditions = sc.preconditions
                    existing.steps = sc.steps
                    existing.expected_result = sc.expected_result
                    existing.db_assertions = sc.db_assertions
                else:
                    new_sc = ScenarioModel(
                        id=sc.id,
                        title=sc.title,
                        description=sc.description,
                        category=sc.category,
                        test_type=sc.test_type,
                        preconditions=sc.preconditions,
                        steps=sc.steps,
                        expected_result=sc.expected_result,
                        db_assertions=sc.db_assertions
                    )
                    db.add(new_sc)
            db.commit()
            logger.info(f"Saved/Updated {len(scenarios)} test scenarios in PostgreSQL.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving scenarios to PostgreSQL: {e}")
        finally:
            db.close()

    @staticmethod
    def save_script(script: GeneratedTestScript) -> Optional[ScriptModel]:
        """Save a generated Playwright test script into PostgreSQL."""
        db = SessionLocal()
        try:
            new_script = ScriptModel(
                scenario_id=script.scenario_id,
                title=script.title,
                test_type=script.test_type,
                file_path=script.file_path,
                page_object_code=script.page_object_code,
                script_code=script.script_code
            )
            db.add(new_script)
            db.commit()
            db.refresh(new_script)
            logger.info(f"Saved script for scenario '{script.scenario_id}' to PostgreSQL.")
            return new_script
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving script to PostgreSQL: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_documents_count() -> int:
        db = SessionLocal()
        try:
            return db.query(DocumentModel).count()
        except Exception:
            return 0
        finally:
            db.close()

    @staticmethod
    def get_scenarios_count() -> int:
        db = SessionLocal()
        try:
            return db.query(ScenarioModel).count()
        except Exception:
            return 0
        finally:
            db.close()

    @staticmethod
    def get_scripts_count() -> int:
        db = SessionLocal()
        try:
            return db.query(ScriptModel).count()
        except Exception:
            return 0
        finally:
            db.close()

    @staticmethod
    def get_all_documents() -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
            return [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "title": d.title,
                    "summary": d.summary,
                    "created_at": str(d.created_at)
                }
                for d in docs
            ]
        finally:
            db.close()

    @staticmethod
    def get_all_scenarios() -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            scs = db.query(ScenarioModel).order_by(ScenarioModel.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "category": s.category,
                    "test_type": s.test_type,
                    "created_at": str(s.created_at)
                }
                for s in scs
            ]
        finally:
            db.close()

    @staticmethod
    def get_all_scripts() -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            scr = db.query(ScriptModel).order_by(ScriptModel.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "scenario_id": s.scenario_id,
                    "title": s.title,
                    "test_type": s.test_type,
                    "file_path": s.file_path,
                    "created_at": str(s.created_at)
                }
                for s in scr
            ]
        finally:
            db.close()
