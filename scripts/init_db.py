"""
Database initialization script for the Agentic AI Test Automation Platform.

This script performs the following tasks:
1. Ensures the PostgreSQL database 'agentic_test_db' exists
2. Creates all database tables using SQLAlchemy models
3. Seeds initial sample insurance claims and payout data for testing

Run this script once after setting up the environment:
    python scripts/init_db.py

The script is idempotent - it will skip seeding if data already exists.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import ensure_database_exists, engine, Base, SessionLocal
from database.models import Claim, Payout
from shared.logger import get_logger

logger = get_logger("scripts.init_db")

def initialize_database():
    """
    Initialize the database with schema and sample data.
    
    This function performs a complete database setup:
    1. Creates the 'agentic_test_db' database if it doesn't exist
    2. Creates all tables defined in SQLAlchemy models
    3. Seeds sample insurance claims data for the demo domain
    
    The function is safe to run multiple times - it checks for existing
    data before seeding to avoid duplicates.
    
    Raises:
        Exception: If database connection or seeding fails
    """
    logger.info("Step 1: Ensuring PostgreSQL database 'agentic_test_db' exists and schemas are updated...")
    ensure_database_exists()
    
    logger.info("Step 2: Creating database tables using SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
    
    logger.info("Step 3: Seeding initial sample claim data into PostgreSQL...")
    db = SessionLocal()
    try:
        existing = db.query(Claim).first()
        if not existing:
            sample_claims = [
                Claim(
                    claim_number="CLM-1001",
                    policy_number="POL-99001",
                    claimant_name="Jane Doe",
                    claim_amount=2500.00,
                    incident_date="2026-05-12",
                    description="Windshield replacement and hood dent repair.",
                    status="SUBMITTED"
                ),
                Claim(
                    claim_number="CLM-1002",
                    policy_number="POL-99002",
                    claimant_name="John Smith",
                    claim_amount=5800.50,
                    incident_date="2026-06-01",
                    description="Rear bumper collision repair.",
                    status="APPROVED"
                ),
                Claim(
                    claim_number="CLM-1003",
                    policy_number="POL-99003",
                    claimant_name="Alice Johnson",
                    claim_amount=12000.00,
                    incident_date="2026-06-15",
                    description="Water damage to home basement.",
                    status="IN_REVIEW"
                )
            ]
            db.add_all(sample_claims)
            db.commit()
            
            approved_claim = db.query(Claim).filter(Claim.claim_number == "CLM-1002").first()
            if approved_claim:
                payout = Payout(
                    claim_id=approved_claim.id,
                    payout_amount=approved_claim.claim_amount,
                    status="PROCESSED"
                )
                db.add(payout)
                db.commit()
                
            logger.info("Sample claims and payouts seeded successfully.")
        else:
            logger.info("Database already contains data. Skipping seed.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()
        
    logger.info("Database initialization completed successfully!")

if __name__ == "__main__":
    initialize_database()
