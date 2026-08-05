from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from configs.config import DATABASE_URL, DEFAULT_DB_URL
import psycopg2
from shared.logger import get_logger

logger = get_logger("database.connection")

Base = declarative_base()

# Primary Database Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_database_exists():
    """Ensure the target PostgreSQL database exists on host, auto-upgrade schemas, and seed initial claim data."""
    from configs.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
    try:
        # Step 1: Ensure database exists
        conn = psycopg2.connect(
            dbname="postgres",
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{POSTGRES_DB}'")
        exists = cursor.fetchone()
        if not exists:
            logger.info(f"Database '{POSTGRES_DB}' does not exist. Creating database...")
            cursor.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
            logger.info(f"Database '{POSTGRES_DB}' created successfully.")
        else:
            logger.info(f"Database '{POSTGRES_DB}' already exists.")
        cursor.close()
        conn.close()

        # Step 2: Ensure schema column upgrades for pre-existing tables
        app_conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        app_conn.autocommit = True
        app_cursor = app_conn.cursor()
        
        # Executions table migrations
        app_cursor.execute("ALTER TABLE IF EXISTS executions ADD COLUMN IF NOT EXISTS video_path VARCHAR(500);")
        app_cursor.execute("ALTER TABLE IF EXISTS executions ADD COLUMN IF NOT EXISTS trace_path VARCHAR(500);")
        app_cursor.execute("ALTER TABLE IF EXISTS executions ADD COLUMN IF NOT EXISTS screenshot_path VARCHAR(500);")
        
        # Documents table migrations
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS title VARCHAR(255);")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS raw_text TEXT;")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS summary TEXT;")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS file_type VARCHAR(50);")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS domain_category VARCHAR(100);")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
        app_cursor.execute("ALTER TABLE IF EXISTS documents ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
        
        app_cursor.close()
        app_conn.close()

        # Step 3: Auto-create tables using Base metadata
        Base.metadata.create_all(bind=engine)
        logger.info("SQLAlchemy metadata table verification complete.")

        # Step 4: Seed initial default data if database is empty
        _seed_initial_claims_and_payouts()

    except Exception as e:
        logger.error(f"Error ensuring database exists and migrating schema: {e}")
        raise e


def _seed_initial_claims_and_payouts():
    """Seed initial claims and payouts into PostgreSQL if claims table is empty."""
    from database.models import Claim, Payout
    db = SessionLocal()
    try:
        if db.query(Claim).count() == 0:
            logger.info("Seeding initial claim records into PostgreSQL...")
            
            c1 = Claim(
                claim_number="CLM-1001",
                policy_number="POL-99001",
                claimant_name="John Doe",
                claim_amount=1500.00,
                incident_date="2026-08-01",
                description="Water damage to kitchen floor",
                status="SUBMITTED"
            )
            c2 = Claim(
                claim_number="CLM-1002",
                policy_number="POL-99002",
                claimant_name="Jane Smith",
                claim_amount=5800.50,
                incident_date="2026-08-02",
                description="Vehicle collision claim",
                status="APPROVED"
            )
            db.add_all([c1, c2])
            db.commit()
            db.refresh(c2)

            p1 = Payout(
                claim_id=c2.id,
                payout_amount=5800.50,
                status="PROCESSED"
            )
            db.add(p1)
            db.commit()
            logger.info("Successfully seeded default claims (CLM-1001, CLM-1002) and payouts.")
    except Exception as e:
        db.rollback()
        logger.warning(f"Seed data insertion skipped or encountered error: {e}")
    finally:
        db.close()

