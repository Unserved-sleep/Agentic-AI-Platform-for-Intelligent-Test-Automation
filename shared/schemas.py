"""
Shared Pydantic Schemas: Data models used across all platform modules.
Defines ParsedRequirement, TestScenario, GeneratedTestScript, ExecutionResult,
SelfHealingResult, and QAReport for consistent data flow between agents.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# --- Document & Requirements ---
class ParsedRequirement(BaseModel):
    document_name: str
    title: str
    summary: str
    actors: List[str] = []
    workflows: List[str] = []
    validations: List[str] = []
    api_endpoints: List[Dict[str, str]] = []
    raw_text: str

# --- Test Scenarios ---
class TestScenario(BaseModel):
    id: str
    title: str
    description: str
    category: str = Field(default="positive", description="positive, negative, boundary, accessibility, security, backend_logic")
    test_type: str = Field(default="UI", description="UI or API")
    preconditions: List[str] = []
    steps: List[str] = []
    expected_result: str
    db_assertions: List[Any] = []

class ScenarioGenerationResponse(BaseModel):
    requirement_summary: str
    scenarios: List[TestScenario]

# --- Playwright Scripts ---
class GeneratedTestScript(BaseModel):
    scenario_id: str
    title: str
    test_type: str  # "UI" or "API"
    page_object_code: Optional[str] = None
    script_code: str
    file_path: str
    db_checks_included: bool = False

# --- Execution ---
class ExecutionRequest(BaseModel):
    script_path: str
    test_type: str = "UI"

class ExecutionResult(BaseModel):
    run_id: str
    script_path: str
    test_type: str
    status: str  # "PASSED", "FAILED", "ERROR"
    duration_seconds: float
    stdout: str
    stderr: str
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    video_path: Optional[str] = None
    failure_reason: Optional[str] = None
    db_assertion_results: List[Dict[str, Any]] = []
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# --- Self Healing ---
class SelfHealingRequest(BaseModel):
    run_id: str
    script_path: str
    failure_reason: str
    stdout: str
    stderr: str

class SelfHealingResult(BaseModel):
    healed: bool
    failure_category: str  # "UI locator drift", "API contract drift", "backend business-logic regression", "environment error"
    original_code: str
    repaired_code: str
    patch_explanation: str
    retry_execution_result: Optional[ExecutionResult] = None

# --- Report & Analytics ---
class QAReport(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate_percentage: float
    ui_tests_count: int
    ui_passed: int
    api_tests_count: int
    api_passed: int
    healed_tests_count: int
    execution_history: List[ExecutionResult] = []
    recommendations: List[str] = []
