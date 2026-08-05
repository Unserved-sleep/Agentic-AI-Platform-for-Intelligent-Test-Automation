import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from database.connection import get_db, ensure_database_exists
from database.models import Claim, Payout, DocumentModel
from database.assertions import DBAssertionHelper

from ingestion.parser import DocumentParser
from rag.pipeline import RAGPipeline
from agents.requirement_agent import RequirementAgent
from agents.test_scenario_agent import TestScenarioAgent
from agents.script_agent import PlaywrightScriptAgent
from agents.report_agent import ReportAgent
from execution.runner import execution_runner
from orchestration.graph import orchestrator
from shared.schemas import ParsedRequirement, ExecutionRequest, SelfHealingRequest
from shared.logger import get_logger

logger = get_logger("backend.main")

# Ensure database exists on app startup
try:
    ensure_database_exists()
except Exception as e:
    logger.warning(f"Could not connect to PostgreSQL database on startup: {e}")

app = FastAPI(
    title="Agentic AI Platform for Intelligent Test Automation API",
    description="Multi-Agent Test Automation Platform with PostgreSQL DB Assertions & Self-Healing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_pipeline = RAGPipeline()
req_agent = RequirementAgent()
scenario_agent = TestScenarioAgent()
script_agent = PlaywrightScriptAgent()
report_agent = ReportAgent()


# --- Platform API Endpoints ---

@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "database": "connected", "platform": "Agentic AI Test Automation"}


@app.post("/api/v1/ingest")
def ingest_document(file_path: Optional[str] = Form(None), db: Session = Depends(get_db)):
    target_path = file_path or "docs/claims_brd.md"
    try:
        parsed = DocumentParser.parse_file(target_path)
        doc_entry = DocumentModel(
            filename=parsed.document_name,
            title=parsed.title,
            raw_text=parsed.raw_text,
            summary=parsed.summary
        )
        db.add(doc_entry)
        db.commit()
        
        # Ingest into RAG pipeline (clearing previous document context)
        rag_pipeline.ingest_document(parsed.document_name, parsed.raw_text, replace_existing=True)
        
        analysis = req_agent.process_requirement(parsed, rag_pipeline=rag_pipeline)
        return {"status": "success", "parsed_requirement": parsed.model_dump(), "analysis": analysis}
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/scenarios/generate")
def generate_scenarios(req_data: Dict[str, Any]):
    scenarios = scenario_agent.generate_scenarios(req_data)
    return {"status": "success", "count": len(scenarios), "scenarios": [s.model_dump() for s in scenarios]}


@app.post("/api/v1/scripts/generate")
def generate_scripts(scenarios: List[Dict[str, Any]]):
    from shared.schemas import TestScenario
    generated = []
    for sc in scenarios:
        sc_obj = TestScenario(**sc)
        script = script_agent.generate_script(sc_obj)
        generated.append(script.model_dump())
    return {"status": "success", "count": len(generated), "scripts": generated}


@app.post("/api/v1/execute")
def execute_test(request: ExecutionRequest):
    result = execution_runner.run_test(request.script_path, test_type=request.test_type)
    return result.model_dump()


@app.post("/api/v1/orchestration/run")
def run_orchestrated_pipeline(file_path: Optional[str] = "docs/claims_brd.md"):
    parsed = DocumentParser.parse_file(file_path)
    rag_pipeline.ingest_document(parsed.document_name, parsed.raw_text, replace_existing=True)
    analysis = req_agent.process_requirement(parsed, rag_pipeline=rag_pipeline)
    workflow_output = orchestrator.run_workflow(analysis)
    return {"status": "completed", "workflow_results": workflow_output}


@app.get("/api/v1/reports")
def get_reports():
    report = report_agent.generate_report()
    return report.model_dump()


# --- Sample Insurance Claims Portal Service Endpoints ---

@app.get("/claims_form", response_class=HTMLResponse)
def get_claims_form():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Claims Submission Portal</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f8; padding: 40px; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #1e293b; margin-top: 0; }
        label { display: block; margin-top: 15px; font-weight: bold; }
        input, select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #2563eb; color: white; border: none; padding: 12px; width: 100%; margin-top: 20px; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .alert { margin-top: 15px; padding: 10px; border-radius: 4px; display: none; }
        .alert-success { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .alert-danger { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Submit Insurance Claim</h2>
        <div id="success_message" class="alert alert-success">Claim Submitted Successfully!</div>
        <div id="error_message" class="alert alert-danger">Claim amount must be greater than 0</div>
        
        <form id="claimForm">
            <label>Policy Number</label>
            <input type="text" id="policy_number" name="policy_number" placeholder="POL-99001" required>
            
            <label>Claimant Name</label>
            <input type="text" id="claimant_name" name="claimant_name" placeholder="Jane Doe" required>
            
            <label>Claim Amount ($)</label>
            <input type="number" id="claim_amount" name="claim_amount" placeholder="2500" required>
            
            <button type="button" id="submit_claim_btn" onclick="submitForm()">Submit Claim</button>
        </form>
    </div>

    <script>
        function submitForm() {
            const policy = document.getElementById('policy_number').value;
            const claimant = document.getElementById('claimant_name').value;
            const amount = parseFloat(document.getElementById('claim_amount').value);
            
            if (amount <= 0) {
                document.getElementById('error_message').style.display = 'block';
                document.getElementById('success_message').style.display = 'none';
                return;
            }
            
            fetch('/api/v1/claims', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    policy_number: policy,
                    claimant_name: claimant,
                    claim_amount: amount,
                    incident_date: '2026-08-04',
                    description: 'Submitted via Claims Web Portal'
                })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('success_message').style.display = 'block';
                document.getElementById('error_message').style.display = 'none';
            });
        }
    </script>
</body>
</html>
"""


@app.get("/api/v1/claims")
def get_claims(db: Session = Depends(get_db)):
    claims = db.query(Claim).all()
    return claims


@app.get("/api/v1/claims/{claim_identifier}")
def get_claim(claim_identifier: str, db: Session = Depends(get_db)):
    if claim_identifier.isdigit():
        claim = db.query(Claim).filter(Claim.id == int(claim_identifier)).first()
    else:
        claim = db.query(Claim).filter(Claim.claim_number == claim_identifier).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_identifier}' not found")
    return claim


@app.post("/api/v1/claims")
def create_claim(payload: Dict[str, Any], db: Session = Depends(get_db)):
    amount = float(payload.get("claim_amount", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Claim amount must be greater than 0")

    claim_num = payload.get("claim_number") or f"CLM-{1000 + db.query(Claim).count() + 1}"
    new_claim = Claim(
        claim_number=claim_num,
        policy_number=payload.get("policy_number", "POL-9999"),
        claimant_name=payload.get("claimant_name", "Anonymous"),
        claim_amount=amount,
        incident_date=payload.get("incident_date", "2026-08-04"),
        description=payload.get("description", "Claim submission"),
        status="SUBMITTED"
    )
    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)
    return new_claim


@app.post("/api/v1/claims/{claim_identifier}/approve")
def approve_claim(claim_identifier: str, db: Session = Depends(get_db)):
    if claim_identifier.isdigit():
        claim = db.query(Claim).filter(Claim.id == int(claim_identifier)).first()
    else:
        claim = db.query(Claim).filter(Claim.claim_number == claim_identifier).first()

    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_identifier}' not found")

    claim.status = "APPROVED"
    db.commit()

    # Business Rule: Create Payout Record upon Approval
    payout = Payout(
        claim_id=claim.id,
        payout_amount=claim.claim_amount,
        status="PROCESSED"
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)

    return {"status": "APPROVED", "claim_id": claim.id, "claim_number": claim.claim_number, "payout": payout}


@app.post("/api/v1/claims/{claim_identifier}/reject")
def reject_claim(claim_identifier: str, db: Session = Depends(get_db)):
    if claim_identifier.isdigit():
        claim = db.query(Claim).filter(Claim.id == int(claim_identifier)).first()
    else:
        claim = db.query(Claim).filter(Claim.claim_number == claim_identifier).first()

    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_identifier}' not found")

    claim.status = "REJECTED"
    db.commit()
    return {"status": "REJECTED", "claim_id": claim.id, "claim_number": claim.claim_number}


@app.get("/api/v1/payouts")
def get_payouts(db: Session = Depends(get_db)):
    payouts = db.query(Payout).all()
    return payouts

