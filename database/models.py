from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(50), unique=True, index=True, nullable=False)
    policy_number = Column(String(50), index=True, nullable=False)
    claimant_name = Column(String(100), nullable=False)
    claim_amount = Column(Float, nullable=False)
    incident_date = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="SUBMITTED", index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    payouts = relationship("Payout", back_populates="claim", cascade="all, delete-orphan")


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=False)
    payout_amount = Column(Float, nullable=False)
    status = Column(String(30), default="PENDING", index=True, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", back_populates="payouts")


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True, nullable=False)
    title = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=True)
    domain_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class ScenarioModel(Base):
    __tablename__ = "scenarios"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), index=True, nullable=False)
    test_type = Column(String(20), index=True, nullable=False)
    preconditions = Column(JSON, nullable=True)
    steps = Column(JSON, nullable=True)
    expected_result = Column(Text, nullable=False)
    db_assertions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScriptModel(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(50), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    test_type = Column(String(20), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    page_object_code = Column(Text, nullable=True)
    script_code = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionModel(Base):
    __tablename__ = "executions"

    id = Column(String(50), primary_key=True, index=True)
    script_path = Column(String(500), nullable=False)
    test_type = Column(String(20), index=True, nullable=False)
    status = Column(String(30), index=True, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    trace_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    failure_reason = Column(Text, nullable=True)
    db_assertion_results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HealingLogModel(Base):
    __tablename__ = "healing_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), index=True, nullable=False)
    failure_category = Column(String(100), nullable=False)
    original_code = Column(Text, nullable=False)
    repaired_code = Column(Text, nullable=False)
    patch_explanation = Column(Text, nullable=False)
    healed_successfully = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

