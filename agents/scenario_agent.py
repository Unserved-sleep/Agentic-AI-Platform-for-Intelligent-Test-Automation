from pydantic_ai import Agent, RunContext
import sys
import os

# Ensure the parent directory is in sys.path to allow imports from models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.test_scenario import ScenarioGenerationResult
from shared.deps import AgentDeps

# Initialize the PydanticAI Agent
# Using a default model, but this can be overridden when running the agent.
# Using 'groq:llama-3.3-70b-versatile' or similar high reasoning model is recommended.
scenario_agent = Agent(
    'groq:llama-3.3-70b-versatile', 
    deps_type=AgentDeps,
    output_type=ScenarioGenerationResult,
    retries=3,
    system_prompt=(
        "You are an Expert QA Automation Engineer and Test Architect. "
        "Your task is to analyze user stories, Business Requirement Documents (BRDs), or API documentation "
        "and generate a COMPREHENSIVE suite of Test Scenarios.\n\n"
        "CRITICAL: You MUST generate AT LEAST ONE test scenario for EVERY subcategory listed below, "
        "where applicable to the given requirement. This means you should produce approximately 20 scenarios. "
        "Do NOT be lazy. Do NOT skip subcategories. If a subcategory is even tangentially applicable, include a scenario for it.\n\n"
        "Categories and their subcategories:\n"
        "1. Positive:\n"
        "   - Happy Path: The standard successful flow.\n"
        "   - Alternate Flow: A valid but non-default path.\n"
        "   - Role Based: Different user roles performing the action.\n"
        "2. Negative:\n"
        "   - Invalid Input: Providing wrong data types or formats.\n"
        "   - Missing Input: Omitting required fields.\n"
        "   - Invalid State: Performing the action when preconditions are not met.\n"
        "3. Boundary:\n"
        "   - Minimum Value: Testing with the smallest allowed value.\n"
        "   - Maximum Value: Testing with the largest allowed value.\n"
        "   - Length: Testing string length limits.\n"
        "   - Numeric Range: Testing numeric boundaries.\n"
        "4. Accessibility:\n"
        "   - Keyboard: Full keyboard navigation support.\n"
        "   - Screen Reader: Screen reader compatibility.\n"
        "   - Focus: Correct focus management.\n"
        "5. Security:\n"
        "   - SQL Injection: Attempting SQL injection attacks.\n"
        "   - XSS: Attempting cross-site scripting.\n"
        "   - CSRF: Cross-site request forgery checks.\n"
        "   - Authentication: Verifying auth is required.\n"
        "   - Authorization: Verifying correct role permissions.\n"
        "   - Session: Session management and timeout.\n"
        "6. Performance:\n"
        "   - Load: High concurrent user load.\n"
        "   - Stress: System behavior beyond capacity.\n\n"
        "You must output tests at the appropriate test_level:\n"
        "- `UI`: Browser tests interacting with the frontend.\n"
        "- `API Contract`: Backend API tests verifying surface-level checks like status codes, request/response schemas, and headers.\n"
        "- `API Backend`: Backend API tests verifying functional business logic, state changes, and data persistence in the database.\n\n"
        "Ensure every scenario has clear steps and unambiguous expected results.\n"
        "If the requirement text is a user story or high-level summary, use the `search_knowledge_base` tool to query for specific backend constraints, policy rules, and detailed documentation."
    )
)

@scenario_agent.tool
def search_knowledge_base(ctx: RunContext[AgentDeps], query: str) -> dict:
    """
    Search the centralized knowledge base (RAG) for documentation, policy guidelines, and business rules.
    Use this to look up constraints (like age limits for insurance) when the user story doesn't specify them.
    
    Args:
        query: The search query string.
    """
    if ctx.deps.rag_retriever:
        return ctx.deps.rag_retriever.retrieve_context(query)
    return {"error": "RAG retriever not initialized."}

def generate_test_scenarios(requirement_text: str, deps: AgentDeps, model: str = None) -> ScenarioGenerationResult:
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

    from execution.browser_agent.browser_execution_agent import BrowserExecutionAgent
    from execution.browser_agent.scenario_prompt_builder import ScenarioPromptBuilder

    browser = BrowserExecutionAgent()
    application_url = os.environ.get("APPLICATION_URL", "http://127.0.0.1:8000")

    summary = browser.inspect_summary(url=application_url)

    prompt = ScenarioPromptBuilder.build(
        requirement=requirement_text,
        inspection=summary,
    )
        
    result = scenario_agent.run_sync(
        prompt,
        deps=deps,
        **kwargs
    )
    return result.output
