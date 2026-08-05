"""
Report Agent: Generates QA analytics and execution summary reports from PostgreSQL.
Queries execution and healing log records to build pass/fail metrics, UI vs API breakdowns,
self-healing counts, and actionable QA recommendations.
"""
from typing import List, Dict, Any
from shared.schemas import QAReport, ExecutionResult
from database.connection import SessionLocal
from database.models import ExecutionModel, HealingLogModel
from shared.logger import get_logger

logger = get_logger("agents.report_agent")

class ReportAgent:
    """Generates execution metrics, UI vs API breakdown, and AI quality reports."""

    def generate_report(self) -> QAReport:
        db = SessionLocal()
        try:
            executions = db.query(ExecutionModel).all()
            healing_logs = db.query(HealingLogModel).all()

            total_tests = len(executions)
            passed_tests = len([e for e in executions if e.status == "PASSED"])
            failed_tests = len([e for e in executions if e.status in ["FAILED", "ERROR"]])
            pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

            ui_executions = [e for e in executions if e.test_type.upper() == "UI"]
            api_executions = [e for e in executions if e.test_type.upper() == "API"]

            ui_passed = len([e for e in ui_executions if e.status == "PASSED"])
            api_passed = len([e for e in api_executions if e.status == "PASSED"])
            healed_count = len([h for h in healing_logs if h.healed_successfully])

            recommendations = []
            if pass_rate < 80.0:
                recommendations.append("Pass rate is below 80%. Investigate recent UI locator changes or API endpoint shifts.")
            if healed_count > 0:
                recommendations.append(f"Self-Healing Agent repaired {healed_count} broken test scripts automatically.")
            if len(api_executions) > 0:
                recommendations.append("API test coverage is active with read-only PostgreSQL DB state assertions.")

            execution_results = [
                ExecutionResult(
                    run_id=e.id,
                    script_path=e.script_path,
                    test_type=e.test_type,
                    status=e.status,
                    duration_seconds=e.duration_seconds,
                    stdout=e.stdout or "",
                    stderr=e.stderr or "",
                    screenshot_path=e.screenshot_path,
                    trace_path=e.trace_path,
                    video_path=e.video_path,
                    failure_reason=e.failure_reason,
                    db_assertion_results=e.db_assertion_results or [],
                    timestamp=str(e.created_at)
                )
                for e in executions
            ]

            return QAReport(
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                pass_rate_percentage=round(pass_rate, 2),
                ui_tests_count=len(ui_executions),
                ui_passed=ui_passed,
                api_tests_count=len(api_executions),
                api_passed=api_passed,
                healed_tests_count=healed_count,
                execution_history=execution_results,
                recommendations=recommendations
            )
        finally:
            db.close()
