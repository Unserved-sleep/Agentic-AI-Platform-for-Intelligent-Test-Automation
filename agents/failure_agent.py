"""
Failure Analysis Agent: Analyzes test execution failures and classifies their root cause.
Inspects stdout, stderr, and traceback output to categorize failures as UI locator drift,
API contract drift, or backend business-logic regressions.
"""
from typing import Dict, Any
from shared.schemas import ExecutionResult
from agents.llm_client import llm_client
from prompts.system_prompts import FAILURE_ANALYSIS_PROMPT
from shared.logger import get_logger

logger = get_logger("agents.failure_agent")

class FailureAnalysisAgent:
    """Analyzes test failures and classifies root cause category using log tracebacks and artifact paths."""

    def analyze_failure(self, result: ExecutionResult) -> Dict[str, Any]:
        prompt = f"""
Test Script: {result.script_path}
Test Type: {result.test_type}
Status: {result.status}
Artifacts Captured:
- Screenshot: {result.screenshot_path}
- Trace Zip: {result.trace_path}
- Video Recording: {result.video_path}

Stdout:
{result.stdout[-1500:]}

Stderr:
{result.stderr[-1500:]}

Failure Reason: {result.failure_reason}
"""
        llm_response = llm_client.generate(prompt, system_prompt=FAILURE_ANALYSIS_PROMPT)

        category = self._classify_error(result.stdout + result.stderr + str(result.failure_reason))

        return {
            "run_id": result.run_id,
            "failure_category": category,
            "analysis_details": llm_response or f"Classified failure as '{category}' based on traceback analysis.",
            "recommendation": f"Apply repair strategy for {category}.",
            "artifacts": {
                "screenshot_path": result.screenshot_path,
                "trace_path": result.trace_path,
                "video_path": result.video_path
            }
        }

    def _classify_error(self, log_content: str) -> str:
        log_lower = log_content.lower()
        if any(term in log_lower for term in ["timeout", "locator", "element not found", "page.locator"]):
            return "UI locator drift"
        elif any(term in log_lower for term in ["status_code", "404", "500", "http", "contract"]):
            return "API contract drift"
        elif any(term in log_lower for term in ["db assertion", "postgresql", "payout assertion", "claim status"]):
            return "backend business-logic regression"
        else:
            return "UI locator drift"
