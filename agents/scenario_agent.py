from pydantic_ai import Agent, RunContext
import sys
import os

# Ensure the parent directory is in sys.path to allow imports from models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.test_scenario import ScenarioGenerationResult

# Initialize the PydanticAI Agent
# Using a default model, but this can be overridden when running the agent.
# Using 'groq:llama-3.3-70b-versatile' or similar high reasoning model is recommended.
scenario_agent = Agent(
    'groq:llama-3.3-70b-versatile', 
    result_type=ScenarioGenerationResult,
    system_prompt=(
        "You are an Expert QA Automation Engineer and Test Architect. "
        "Your task is to analyze user stories, Business Requirement Documents (BRDs), or API documentation "
        "and generate a comprehensive suite of Test Scenarios.\n\n"
        "You must generate test cases covering the following categories:\n"
        "1. Positive (Happy Path, Alternate Flow, Role Based)\n"
        "2. Negative (Invalid Input, Missing Input, Invalid State)\n"
        "3. Boundary (Minimum Value, Maximum Value, Length, Numeric Range)\n"
        "4. Accessibility (Keyboard, Screen Reader, Focus)\n"
        "5. Security (SQL Injection, XSS, CSRF, Authentication, Authorization, Session)\n"
        "6. Performance (Load, Stress)\n\n"
        "You must ensure to output both UI/Browser tests (is_api=False) AND backend API tests (is_api=True) if applicable to the requirements. "
        "API tests should verify backend business logic, state changes in the database, and API contracts. "
        "Ensure every scenario has clear steps and unambiguous expected results."
    )
)

def generate_test_scenarios(requirement_text: str, model: str = None) -> ScenarioGenerationResult:
    """
    Generate test scenarios given a requirement text.
    
    Args:
        requirement_text (str): The context (User story, BRD extract, etc.)
        model (str, optional): The model to use. Defaults to the agent's default.
    
    Returns:
        ScenarioGenerationResult: The generated list of test scenarios.
    """
    kwargs = {}
    if model:
        kwargs['model'] = model
        
    result = scenario_agent.run_sync(
        f"Generate test scenarios based on the following requirement:\n\n{requirement_text}",
        **kwargs
    )
    return result.data
