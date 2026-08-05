"""
Database Assertion Helper: Read-only PostgreSQL assertions for API test validation.
Enables tests to verify claim status transitions, payout creation, and other
backend state changes directly against the database.
"""
from typing import Dict, Any, Optional, List
from database.connection import SessionLocal
from database.models import Claim, Payout
from shared.logger import get_logger

logger = get_logger("database.assertions")

class DBAssertionHelper:
    """
    Read-only Database Assertion Helper.
    Exposes helper functions to inspect PostgreSQL state for claims, payouts, and status transitions.
    """

    @staticmethod
    def get_claim_by_number(claim_number: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            claim = db.query(Claim).filter(Claim.claim_number == claim_number).first()
            if not claim:
                return None
            return {
                "id": claim.id,
                "claim_number": claim.claim_number,
                "policy_number": claim.policy_number,
                "claimant_name": claim.claimant_name,
                "claim_amount": claim.claim_amount,
                "status": claim.status,
                "created_at": str(claim.created_at),
                "updated_at": str(claim.updated_at)
            }
        finally:
            db.close()

    @staticmethod
    def assert_claim_status(claim_number: str, expected_status: str) -> Dict[str, Any]:
        claim = DBAssertionHelper.get_claim_by_number(claim_number)
        if not claim:
            return {
                "assertion": "assert_claim_status",
                "success": False,
                "claim_number": claim_number,
                "message": f"Claim '{claim_number}' not found in database."
            }
        
        passed = (claim["status"].upper() == expected_status.upper())
        return {
            "assertion": "assert_claim_status",
            "success": passed,
            "claim_number": claim_number,
            "actual_status": claim["status"],
            "expected_status": expected_status,
            "message": f"Claim status is '{claim['status']}', expected '{expected_status}'." if passed else f"Status mismatch: actual '{claim['status']}', expected '{expected_status}'."
        }

    @staticmethod
    def get_payouts_for_claim(claim_id: int) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            payouts = db.query(Payout).filter(Payout.claim_id == claim_id).all()
            return [
                {
                    "id": p.id,
                    "claim_id": p.claim_id,
                    "payout_amount": p.payout_amount,
                    "status": p.status,
                    "processed_at": str(p.processed_at)
                }
                for p in payouts
            ]
        finally:
            db.close()

    @staticmethod
    def assert_payout_created(claim_number: str, expected_amount: Optional[float] = None) -> Dict[str, Any]:
        claim = DBAssertionHelper.get_claim_by_number(claim_number)
        if not claim:
            return {
                "assertion": "assert_payout_created",
                "success": False,
                "claim_number": claim_number,
                "message": f"Claim '{claim_number}' not found in database."
            }
        
        payouts = DBAssertionHelper.get_payouts_for_claim(claim["id"])
        if not payouts:
            return {
                "assertion": "assert_payout_created",
                "success": False,
                "claim_number": claim_number,
                "message": f"No payout records found for claim ID {claim['id']} ({claim_number})."
            }
        
        latest_payout = payouts[-1]
        amount_match = True if expected_amount is None else (abs(latest_payout["payout_amount"] - expected_amount) < 0.01)
        
        return {
            "assertion": "assert_payout_created",
            "success": amount_match,
            "claim_number": claim_number,
            "payout": latest_payout,
            "message": f"Payout of ${latest_payout['payout_amount']} found for claim {claim_number}." if amount_match else f"Payout amount mismatch: expected {expected_amount}, got {latest_payout['payout_amount']}."
        }

    @staticmethod
    def get_claim_by_id(claim_id: int) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                return None
            return {
                "id": claim.id,
                "claim_number": claim.claim_number,
                "policy_number": claim.policy_number,
                "claimant_name": claim.claimant_name,
                "claim_amount": claim.claim_amount,
                "status": claim.status,
                "created_at": str(claim.created_at),
                "updated_at": str(claim.updated_at)
            }
        finally:
            db.close()

    @staticmethod
    def assert_claim_exists(claim_number: str) -> Dict[str, Any]:
        claim = DBAssertionHelper.get_claim_by_number(claim_number)
        exists = claim is not None
        return {
            "assertion": "assert_claim_exists",
            "success": exists,
            "claim_number": claim_number,
            "claim": claim,
            "message": f"Claim '{claim_number}' exists in database." if exists else f"Claim '{claim_number}' not found in database."
        }

    @staticmethod
    def assert_table_row_count(table_name: str, min_count: int = 1) -> Dict[str, Any]:
        from database.models import Claim, Payout, DocumentModel, ScenarioModel, ScriptModel, ExecutionModel, HealingLogModel
        model_map = {
            "claims": Claim,
            "payouts": Payout,
            "documents": DocumentModel,
            "scenarios": ScenarioModel,
            "scripts": ScriptModel,
            "executions": ExecutionModel,
            "healing_logs": HealingLogModel
        }
        model = model_map.get(table_name.lower())
        if not model:
            return {
                "assertion": "assert_table_row_count",
                "success": False,
                "table_name": table_name,
                "message": f"Unknown table name '{table_name}'."
            }
        
        db = SessionLocal()
        try:
            count = db.query(model).count()
            passed = count >= min_count
            return {
                "assertion": "assert_table_row_count",
                "success": passed,
                "table_name": table_name,
                "actual_count": count,
                "min_count": min_count,
                "message": f"Table '{table_name}' has {count} rows (expected >= {min_count})." if passed else f"Table '{table_name}' has {count} rows, expected at least {min_count}."
            }
        finally:
            db.close()

