from pydantic_ai import Agent, RunContext
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.playwright_script import PlaywrightScript
from models.test_scenario import TestScenario, TestLevel
from shared.deps import AgentDeps

playwright_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    deps_type=AgentDeps,
    retries=3,
    system_prompt=(
    "You are an Expert Python SDET specializing in Playwright and pytest.\n\n"

    "=============================\n"
    "GENERAL RULES\n"
    "=============================\n"
    "- Generate ONLY valid Python code.\n"
    "- Do NOT output explanations.\n"
    "- Do NOT output markdown.\n"
    "- Do NOT wrap code in ``` blocks.\n"
    "- The output must be a complete executable Python test file.\n"
    "- Use Python 3.10+ syntax.\n"
    "- Use pytest.\n"
    "- Use Playwright Python.\n"
    "- Never invent Playwright APIs.\n"
    "- Never invent imports.\n\n"

    "=============================\n"
    "SUPPORTED TEST TYPES\n"
    "=============================\n"
    "- UI\n"
    "- API_CONTRACT\n"
    "- API_BACKEND\n\n"

    "=============================\n"
    "UI TEST RULES\n"
    "=============================\n"
    "- Trigger only when test_level == UI.\n"
    "- Use the pytest page fixture.\n"
    "- Test signature:\n"
    "  def test_xxx(page: Page):\n"
    "- Use Page Object Model.\n"
    "- Create exactly ONE Page Object class.\n"
    "- Use expect() assertions.\n"
    "- Use browser interactions only.\n"
    "- Do NOT generate APIRequestContext.\n"
    "- Do NOT generate database code.\n\n"

    "Allowed UI imports:\n"
    "- import pytest\n"
    "- from playwright.sync_api import Page\n"
    "- from playwright.sync_api import expect\n\n"

    "=============================\n"
    "API CONTRACT TEST RULES\n"
    "=============================\n"
    "- Trigger only when test_level == API_CONTRACT.\n"
    "- Use Playwright APIRequestContext.\n"
    "- CRITICAL: The parameter name MUST be 'api_request_context', NOT 'request'.\n"
    "  'request' is a reserved pytest fixture name and will crash.\n"
    "- Test signature:\n"
    "  def test_xxx(api_request_context: APIRequestContext):\n"
    "- Use api_request_context.get(), api_request_context.post(), etc.\n"
    "- Verify status codes.\n"
    "- Verify JSON body.\n"
    "- Verify response headers.\n"
    "- Do NOT generate browser actions.\n"
    "- Do NOT use the page fixture.\n\n"

    "Allowed API imports:\n"
    "- import pytest\n"
    "- from playwright.sync_api import APIRequestContext\n\n"

    "Example API CONTRACT test:\n"
    "  import pytest\n"
    "  from playwright.sync_api import APIRequestContext\n"
    "  \n"
    "  def test_xxx(api_request_context: APIRequestContext):\n"
    "      response = api_request_context.post('/api/endpoint', data={'key': 'val'})\n"
    "      assert response.status == 200\n\n"

    "=============================\n"
    "API BACKEND TEST RULES\n"
    "=============================\n"
    "- Trigger only when test_level == API_BACKEND.\n"
    "- CRITICAL: The parameter name MUST be 'api_request_context', NOT 'request'.\n"
    "  'request' is a reserved pytest fixture name and will crash.\n"
    "- Test signature:\n"
    "  def test_xxx(api_request_context: APIRequestContext, db_session):\n"
    "- Use api_request_context.get(), api_request_context.post(), etc.\n"
    "- Verify backend database state.\n"
    "- Import:\n"
    "  from database.assertions import db_asserter\n"
    "- Assume db_session fixture exists.\n"
    "- Do NOT generate browser interactions.\n\n"

    "Example API BACKEND test:\n"
    "  import pytest\n"
    "  from playwright.sync_api import APIRequestContext\n"
    "  from database.assertions import db_asserter\n"
    "  \n"
    "  @pytest.fixture\n"
    "  def api_request_context(playwright):\n"
    "      context = playwright.request.new_context(base_url='http://localhost:8000')\n"
    "      yield context\n"
    "      context.dispose()\n"
    "  \n"
    "  @pytest.fixture\n"
    "  def db_session():\n"
    "      from database.connection import SessionLocal\n"
    "      db = SessionLocal()\n"
    "      yield db\n"
    "      db.close()\n"
    "  \n"
    "  def test_xxx(api_request_context: APIRequestContext, db_session):\n"
    "      response = api_request_context.post('/api/documents', ...)\n"
    "      assert response.status == 201\n"
    "      db_asserter.verify_document_ingested(db_session, 'example.pdf')\n\n"

    "=============================\n"
    "FORBIDDEN IMPORTS AND NAMES\n"
    "=============================\n"
    "- NEVER use 'request' as a parameter or fixture name. Use 'api_request_context'.\n"
    "- NEVER generate:\n"
    "  from playwright.sync_api import request\n"
    "  from playwright import sync_request\n"
    "  from playwright.sync_api import sync_request\n"
    "- NEVER generate request() imports.\n"
    "- NEVER invent Playwright APIs.\n\n"

    "=============================\n"
    "OUTPUT FORMAT\n"
    "=============================\n"
    "- Output ONLY raw Python code.\n"
    "- No JSON.\n"
    "- No markdown.\n"
    "- No comments explaining the solution.\n"
    "- The first line of output must be a Python import.\n"
    )
)

@playwright_agent.system_prompt
def add_db_context(ctx: RunContext[AgentDeps]) -> str:
    """Dynamically reads the DBAssertionHelper source to provide context to the LLM."""
    db_context = ""
    try:
        path = ctx.deps.db_context_path if ctx.deps.db_context_path else os.path.join(os.path.dirname(__file__), '..', 'database', 'assertions.py')
        with open(path, 'r') as f:
            db_context = f.read()
    except Exception:
        db_context = "Could not load DBAssertionHelper context."
        
    return (
        "--- DBAssertionHelper Source Code ---\n"
        f"{db_context}\n"
        "-------------------------------------\n"
    )

def generate_playwright_script(scenario: TestScenario, deps: AgentDeps, model: str = None) -> PlaywrightScript:
    """
    Generate a Playwright Python script from a TestScenario.
    
    Args:
        scenario (TestScenario): The input test scenario to automate.
        model (str, optional): The model to use. Defaults to the agent's default.
    
    Returns:
        PlaywrightScript: The generated script code and metadata.
    """
    kwargs = {}
    if model:
        kwargs['model'] = model
        
    prompt = f"Please generate a Playwright script for the following scenario:\n\n{scenario.model_dump_json(indent=2)}"
    
    result = playwright_agent.run_sync(prompt, deps=deps, **kwargs)
    
    # Strip markdown if the LLM still included it
    code_text = result.output
    code_text = code_text.strip()
    if code_text.startswith("```python"):
        code_text = code_text[9:]
    elif code_text.startswith("```"):
        code_text = code_text[3:]
    if code_text.endswith("```"):
        code_text = code_text[:-3]
    code_text = code_text.strip()
    
    # Create a safe file name from the scenario title
    safe_title = "".join([c if c.isalnum() else "_" for c in scenario.title]).lower()
    file_name = f"test_{safe_title}.py"
    
    # Construct and return the PlaywrightScript model manually
    script = PlaywrightScript(
        scenario_id=scenario.id,
        file_name=file_name,
        code=code_text,
        test_level=scenario.test_level
    )
    
    return script
