from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

class FailureCategory(str, Enum):
    UI_LOCATOR_DRIFT = "UI_LOCATOR_DRIFT"
    API_CONTRACT_DRIFT = "API_CONTRACT_DRIFT"
    BACKEND_LOGIC_BUG = "BACKEND_LOGIC_BUG"
    SCRIPT_SYNTAX_ERROR = "SCRIPT_SYNTAX_ERROR"
    ENVIRONMENT_ISSUE = "ENVIRONMENT_ISSUE"
    UNKNOWN = "UNKNOWN"

class FailureDiagnosis(BaseModel):
    category: FailureCategory = Field(
        ..., 
        description="The categorization of the failure based on the logs."
    )
    root_cause_explanation: str = Field(
        ..., 
        description="A brief explanation of why the test failed."
    )
    is_script_repairable: bool = Field(
        ..., 
        description="True if the test script can be repaired (e.g. locator fix, syntax fix). False if it is an actual application bug or unrecoverable environment issue."
    )
    repair_instructions: Optional[str] = Field(
        None, 
        description="Specific instructions for the script generator to fix the script, if it is repairable."
    )

failure_analysis_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    retries=3,
    system_prompt=(
        "You are an Expert QA Automation Architect specializing in failure triage and root cause analysis.\n"
        "Your task is to analyze failed Playwright test execution logs and the corresponding test script, "
        "and output a structured diagnosis.\n\n"
        "Categorization Rules:\n"
        "1. UI_LOCATOR_DRIFT: The script failed because an element could not be found, timed out waiting for an element, or strict mode violation. This means the UI changed and the test needs updating.\n"
        "2. API_CONTRACT_DRIFT: An API request failed because the response schema changed, status code changed from expected, or endpoint is not found (404), but it's an expected contract evolution that the test needs to adapt to.\n"
        "3. BACKEND_LOGIC_BUG: The script correctly executes the steps and assertions, but the application returns the wrong data (e.g., 500 error, or functional assertion failure like 'Expected True but got False' indicating a real bug). The script is fine, the app is broken.\n"
        "4. SCRIPT_SYNTAX_ERROR: The python script has a syntax error, fixture mismatch, or indentation error. It failed during pytest collection or compilation.\n"
        "5. ENVIRONMENT_ISSUE: The browser failed to launch, network timeout, or connection refused.\n\n"
        "IMPORTANT: If the failure is a BACKEND_LOGIC_BUG or ENVIRONMENT_ISSUE, you MUST set `is_script_repairable` to false. "
        "If it's UI_LOCATOR_DRIFT, API_CONTRACT_DRIFT, or SCRIPT_SYNTAX_ERROR, you MUST set `is_script_repairable` to true, and provide detailed `repair_instructions` so the next agent can rewrite the script.\n\n"
        "YOU MUST OUTPUT ONLY VALID RAW JSON matching the following schema. NO MARKDOWN, NO TAGS, NO <function> WRAPPER:\n"
        "{\n"
        "  \"category\": \"<one of the categories above>\",\n"
        "  \"root_cause_explanation\": \"<brief explanation>\",\n"
        "  \"is_script_repairable\": <true or false>,\n"
        "  \"repair_instructions\": \"<instructions or null>\"\n"
        "}"
    )
)

def analyze_failure(script_code: str, stdout: str, stderr: str, model: str = None) -> FailureDiagnosis:
    """
    Analyze a test failure and return a structured diagnosis.
    """
    import json
    prompt = f"Script Code:\n{script_code}\n\nStdout:\n{stdout}\n\nStderr:\n{stderr}"
    kwargs = {}
    if model:
        kwargs['model'] = model
        
    result = failure_analysis_agent.run_sync(prompt, **kwargs)
    raw_output = result.output
    
    # Strip any potential tags or markdown
    raw_output = raw_output.strip()
    if raw_output.startswith("```json"):
        raw_output = raw_output.split("```json")[1]
    if raw_output.endswith("```"):
        raw_output = raw_output.rsplit("```", 1)[0]
    if raw_output.startswith("<function=final_result>"):
        raw_output = raw_output.split("<function=final_result>")[1]
    if raw_output.endswith("</function>"):
        raw_output = raw_output.rsplit("</function>", 1)[0]
        
    raw_output = raw_output.strip()
    data = json.loads(raw_output)
    return FailureDiagnosis(**data)
