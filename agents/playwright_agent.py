from pydantic_ai import Agent
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.playwright_script import PlaywrightScript
from models.test_scenario import TestScenario

playwright_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    result_type=PlaywrightScript,
    system_prompt=(
        "You are an Expert SDET (Software Development Engineer in Test). "
        "Your task is to take a structured TestScenario and translate it into a production-ready Playwright Python script.\n\n"
        "Requirements:\n"
        "1. Framework: You MUST write the code for `pytest` using `pytest-playwright`.\n"
        "2. Architecture: You MUST implement the Page Object Model (POM). Define a Page class at the top of the file, or assume it will be separated later. Include clear selectors and action methods.\n"
        "3. Assertions: Use standard Playwright `expect` assertions (e.g., `expect(page.locator('.status')).to_have_text('APPROVED')`).\n"
        "4. Output format: Provide the complete, raw python code as a string in the `code` field of the result. Do NOT wrap it in markdown code blocks inside the string itself (no ```python ... ``` in the JSON).\n"
        "5. API Tests: If the TestScenario is marked as an API test (is_api=True), DO NOT use the browser/page fixtures. Instead, use Playwright's `APIRequestContext` fixture (e.g., `def test_api(request: APIRequestContext):`) to call endpoints directly, and add backend SQL assertion comments.\n\n"
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
    
    # Enforce scenario_id linking
    result.data.scenario_id = scenario.id
    result.data.is_api = scenario.is_api
    
    return result.data
