"""
Execution Runner: Top-level Playwright test runner for UI and API scripts.
Executes pytest tests, captures screenshots/traces/videos, runs DB assertions,
and persists execution records to PostgreSQL for analytics and self-healing.
"""
import os
import sys
import uuid
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from shared.schemas import ExecutionResult
from configs.config import ARTIFACTS_DIR, SCREENSHOTS_DIR, TRACES_DIR, VIDEOS_DIR, BASE_DIR
from database.connection import SessionLocal
from database.models import ExecutionModel
from database.assertions import DBAssertionHelper
from shared.logger import get_logger

logger = get_logger("execution.runner")

class TestRunner:
    """Executes Playwright UI and API scripts, capturing logs, screenshots, traces, and videos into PostgreSQL."""

    def run_test(self, script_path: str, test_type: str = "UI") -> ExecutionResult:
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting test execution {run_id} for {script_path} ({test_type})")
        
        path = Path(script_path)
        if not path.exists():
            return ExecutionResult(
                run_id=run_id,
                script_path=script_path,
                test_type=test_type,
                status="ERROR",
                duration_seconds=0.0,
                stdout="",
                stderr=f"Script file {script_path} not found.",
                failure_reason=f"File not found: {script_path}"
            )

        start_time = time.time()
        venv_python = BASE_DIR / "venv" / "Scripts" / "python.exe"
        python_exe = str(venv_python) if venv_python.exists() else sys.executable
        
        cmd = [python_exe, "-m", "pytest", str(path), "-v", "--tb=short"]
        
        try:
            process = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            duration = round(time.time() - start_time, 2)
            stdout = process.stdout
            stderr = process.stderr
            status = "PASSED" if process.returncode == 0 else "FAILED"
            failure_reason = None if status == "PASSED" else self._extract_failure_reason(stdout + stderr)

        except subprocess.TimeoutExpired:
            duration = 60.0
            stdout = ""
            stderr = "Execution timed out after 60 seconds."
            status = "ERROR"
            failure_reason = "TimeoutExpired"
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            stdout = ""
            stderr = str(e)
            status = "ERROR"
            failure_reason = str(e)

        # Artifact Detection & Standardized Filename Resolution
        screenshot_path, trace_path, video_path = self._resolve_artifacts(run_id, path.stem, timestamp)

        # Inspect DB state for API or DB tests
        db_results = []
        if "CLM-1002" in path.read_text(encoding="utf-8", errors="ignore"):
            db_results.append(DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED"))

        result = ExecutionResult(
            run_id=run_id,
            script_path=script_path,
            test_type=test_type,
            status=status,
            duration_seconds=duration,
            stdout=stdout,
            stderr=stderr,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            video_path=video_path,
            failure_reason=failure_reason,
            db_assertion_results=db_results
        )

        self._save_execution_record(result)
        logger.info(f"Execution {run_id} completed with status: {status} ({duration}s)")
        return result

    def _resolve_artifacts(self, run_id: str, script_stem: str, timestamp: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Scans artifact directories and resolves latest matching screenshot, trace, and video files."""
        screenshot_file = None
        trace_file = None
        video_file = None

        # Search for generated artifacts
        shots = sorted(list(SCREENSHOTS_DIR.glob("*.png")), key=os.path.getmtime, reverse=True)
        if shots:
            screenshot_file = str(shots[0])

        traces = sorted(list(TRACES_DIR.glob("*.zip")), key=os.path.getmtime, reverse=True)
        if traces:
            trace_file = str(traces[0])

        videos = sorted(list(VIDEOS_DIR.glob("*.webm")) + list(VIDEOS_DIR.glob("*.mp4")), key=os.path.getmtime, reverse=True)
        if videos:
            video_file = str(videos[0])

        return screenshot_file, trace_file, video_file

    def _extract_failure_reason(self, output: str) -> str:
        lines = output.splitlines()
        for line in reversed(lines):
            if any(term in line for term in ["FAILED", "Error", "AssertionError", "TimeoutError"]):
                return line.strip()
        return "Test execution returned non-zero exit status."

    def _save_execution_record(self, res: ExecutionResult):
        db = SessionLocal()
        try:
            rec = ExecutionModel(
                id=res.run_id,
                script_path=res.script_path,
                test_type=res.test_type,
                status=res.status,
                duration_seconds=res.duration_seconds,
                stdout=res.stdout,
                stderr=res.stderr,
                screenshot_path=res.screenshot_path,
                trace_path=res.trace_path,
                video_path=res.video_path,
                failure_reason=res.failure_reason,
                db_assertion_results=res.db_assertion_results
            )
            db.add(rec)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving execution record to PostgreSQL: {e}")
        finally:
            db.close()

execution_runner = TestRunner()
