from pydantic_ai import Agent
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.playwright_script import PlaywrightScript
from models.test_scenario import TestScenario, TestLevel

def get_db_assertion_context() -> str:
    """Reads the DBAssertionHelper source to provide context to the LLM."""
    try:
        assertions_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'assertions.py')
        with open(assertions_path, 'r') as f:
            return f.read()
    except Exception:
        return "Could not load DBAssertionHelper context."

db_context = get_db_assertion_context()

playwright_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    retries=3,
    system_prompt=(
        "You are an Expert SDET (Software Development Engineer in Test). "
        "Your task is to take a structured TestScenario and translate it into a production-ready Playwright Python script.\n\n"
        "Requirements:\n"
        "1. Framework: You MUST write the code for `pytest` using `pytest-playwright`.\n"
        "2. UI Tests (`test_level` = UI): Implement the Page Object Model (POM). Define a Page class at the top of the file. Use `page` fixture and standard `expect` assertions.\n"
        "3. API Contract Tests (`test_level` = API_CONTRACT): Do NOT use browser fixtures. Use Playwright's `request` fixture (APIRequestContext) to call endpoints and verify HTTP status codes, JSON schemas, headers, etc.\n"
        "4. API Backend Tests (`test_level` = API_BACKEND): Use `request` fixture to trigger the backend action. Then, you MUST verify the database state using the provided DBAssertionHelper.\n\n"
        "--- DBAssertionHelper Source Code ---\n"
        f"{db_context}\n"
        "-------------------------------------\n\n"
        "When writing API_BACKEND tests, you must import the helper like this:\n"
        "`from database.assertions import db_asserter`\n"
        "And use it appropriately with a mocked or injected DB session (e.g. assume a `db_session` fixture exists if needed, or instantiate it if the helper handles it).\n\n"
        "5. Output format: You must output ONLY the raw Python code. Do NOT output JSON. Do NOT wrap the string in markdown code blocks (e.g., no ```python ... ```). The output must ONLY contain valid python code, nothing else.\n"
        "Always ensure your code includes necessary imports (e.g., `import pytest`, `from playwright.sync_api import Page, expect`)."
    )
)

def generate_playwright_script(scenario: TestScenario, model: str = None) -> PlaywrightScript:
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
    
    result = playwright_agent.run_sync(prompt, **kwargs)
    
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
