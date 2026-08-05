import os
from pathlib import Path
from shared.schemas import ExecutionResult, SelfHealingResult
from agents.failure_agent import FailureAnalysisAgent
from agents.llm_client import llm_client
from prompts.system_prompts import SELF_HEALING_PROMPT
from database.connection import SessionLocal
from database.models import HealingLogModel
from shared.logger import get_logger

logger = get_logger("agents.self_healing_agent")

class SelfHealingAgent:
    """Repairs broken test scripts (locators/assertions) and re-executes tests."""

    def __init__(self):
        self.failure_agent = FailureAnalysisAgent()

    def heal_test(self, result: ExecutionResult, execution_runner) -> SelfHealingResult:
        logger.info(f"Initiating Self-Healing for test run {result.run_id} ({result.script_path})")
        
        # Step 1: Diagnose Failure
        diagnosis = self.failure_agent.analyze_failure(result)
        category = diagnosis["failure_category"]
        
        # Step 2: Read original script content
        script_path = Path(result.script_path)
        if not script_path.exists():
            return SelfHealingResult(
                healed=False,
                failure_category="environment error",
                original_code="",
                repaired_code="",
                patch_explanation=f"Script file {result.script_path} not found."
            )
            
        original_code = script_path.read_text(encoding="utf-8")
        
        # Step 3: Generate repaired script
        repaired_code, explanation = self._apply_repair(original_code, category, result)
        
        # Write repaired script
        script_path.write_text(repaired_code, encoding="utf-8")
        logger.info(f"Wrote repaired script to {script_path}")
        
        # Step 4: Re-execute Test (Retry Loop)
        logger.info(f"Re-executing test {script_path} post-healing...")
        retry_result = execution_runner.run_test(str(script_path), test_type=result.test_type)
        
        healed_success = (retry_result.status == "PASSED")
        
        # Step 5: Save Audit Log to PostgreSQL
        self._record_healing_log(
            run_id=result.run_id,
            category=category,
            original_code=original_code,
            repaired_code=repaired_code,
            explanation=explanation,
            healed=healed_success
        )
        
        return SelfHealingResult(
            healed=healed_success,
            failure_category=category,
            original_code=original_code,
            repaired_code=repaired_code,
            patch_explanation=explanation,
            retry_execution_result=retry_result
        )

    def _apply_repair(self, original_code: str, category: str, result: ExecutionResult) -> tuple[str, str]:
        prompt = f"""
Original Python Script:
{original_code}

Failure Category: {category}
Log Output:
{result.stdout + result.stderr}

Fix the broken locator or assertion and output ONLY valid Python code.
"""
        llm_fix = llm_client.generate(prompt, system_prompt=SELF_HEALING_PROMPT)
        
        if llm_fix and "def test_" in llm_fix:
            # Clean markdown formatting if present
            clean_code = llm_fix.replace("```python", "").replace("```", "").strip()
            return clean_code, f"Repaired script via Groq LLM based on {category} diagnostic."
            
        # Fallback deterministic repair strategies
        repaired_code = original_code
        explanation = ""
        
        if category == "UI locator drift":
            # Upgrade outdated locator or fallback to text selector
            if "#submit_claim_btn" in original_code:
                repaired_code = original_code.replace('#submit_claim_btn', 'button:has-text("Submit Claim"), #submit_claim_btn')
                explanation = "Updated locator '#submit_claim_btn' to include robust text fallback 'button:has-text(\"Submit Claim\")'."
            elif "#policy_number" in original_code:
                repaired_code = original_code.replace('#policy_number', 'input[name="policy_number"], #policy_number')
                explanation = "Updated locator '#policy_number' with attribute fallback."
            else:
                repaired_code = original_code.replace('timeout=5000', 'timeout=15000')
                explanation = "Increased Playwright locator timeout to 15,000ms."
        elif category == "API contract drift":
            repaired_code = original_code.replace('assert response.status_code == 200', 'assert response.status_code in [200, 201]')
            explanation = "Updated HTTP status code assertion from 200 to allow [200, 201]."
        else:
            repaired_code = original_code
            explanation = "No automatic patch pattern matched."

        return repaired_code, explanation

    def _record_healing_log(self, run_id: str, category: str, original_code: str, repaired_code: str, explanation: str, healed: bool):
        db = SessionLocal()
        try:
            log_entry = HealingLogModel(
                run_id=run_id,
                failure_category=category,
                original_code=original_code,
                repaired_code=repaired_code,
                patch_explanation=explanation,
                healed_successfully=healed
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging self-healing record to DB: {e}")
        finally:
            db.close()
