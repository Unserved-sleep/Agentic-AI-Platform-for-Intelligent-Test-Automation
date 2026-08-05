import json
import uuid
from typing import List, Dict, Any
from shared.schemas import TestScenario
from agents.llm_client import llm_client
from prompts.system_prompts import TEST_SCENARIO_PROMPT
from shared.logger import get_logger

logger = get_logger("agents.test_scenario_agent")

class TestScenarioAgent:
    """Generates UI test scenarios targeting https://www.saucedemo.com/ and API test scenarios targeting FastAPI backend + PostgreSQL."""

    def generate_scenarios(self, context: Dict[str, Any]) -> List[TestScenario]:
        has_apis = bool(context.get('api_endpoints'))
        prompt = f"""
Requirement Context:
Title: {context.get('title')}
Workflows: {context.get('workflows')}
Validations: {context.get('validations')}
API Endpoints: {context.get('api_endpoints')}

Generate comprehensive test scenarios for document '{context.get('document_name', 'Requirement')}':
- UI scenarios targeting Swag Labs at https://www.saucedemo.com/ or document workflow validation
- API scenarios targeting backend endpoints ONLY IF API Endpoints list above is NOT empty.
{"CRITICAL: The document context contains NO API endpoints. Do NOT generate any API scenarios." if not has_apis else ""}

Format output as a JSON array of objects with keys: title, description, category, test_type, preconditions, steps, expected_result, db_assertions.
"""
        llm_response = llm_client.generate(prompt, system_prompt=TEST_SCENARIO_PROMPT)
        
        parsed_scenarios = self._try_parse_json(llm_response)
        if not parsed_scenarios:
            logger.info("Using baseline scenario suite.")
            parsed_scenarios = self._get_default_scenarios(has_apis=has_apis)

        scenarios = []
        for item in parsed_scenarios:
            test_type = str(item.get("test_type", "UI")).upper()
            if not has_apis and test_type == "API":
                continue

            scenario_id = item.get("id") or f"SCEN-{uuid.uuid4().hex[:6].upper()}"
            preconditions_val = item.get("preconditions", [])
            if not isinstance(preconditions_val, list):
                preconditions_val = [str(preconditions_val)] if preconditions_val else []

            steps_val = item.get("steps", [])
            if not isinstance(steps_val, list):
                steps_val = [str(steps_val)] if steps_val else []

            db_assertions_val = item.get("db_assertions", [])
            if not isinstance(db_assertions_val, list):
                db_assertions_val = [str(db_assertions_val)] if db_assertions_val else []

            scenario = TestScenario(
                id=scenario_id,
                title=item.get("title", "Test Scenario"),
                description=item.get("description", "Description"),
                category=str(item.get("category", "positive")).lower(),
                test_type=test_type,
                preconditions=preconditions_val,
                steps=steps_val,
                expected_result=item.get("expected_result", "Expected success"),
                db_assertions=db_assertions_val
            )
            scenarios.append(scenario)

        if not any(s.test_type == "UI" for s in scenarios):
            default_items = self._get_default_scenarios(has_apis=False)
            for item in default_items:
                scenarios.append(TestScenario(
                    id=item.get("id") or f"SCEN-{uuid.uuid4().hex[:6].upper()}",
                    title=item.get("title", "UI Test Scenario"),
                    description=item.get("description", "Description"),
                    category=str(item.get("category", "positive")).lower(),
                    test_type="UI",
                    preconditions=item.get("preconditions", []),
                    steps=item.get("steps", []),
                    expected_result=item.get("expected_result", "Expected success"),
                    db_assertions=[]
                ))

        # Persist Test Scenarios to PostgreSQL
        try:
            from database.persistence import DBPersistenceHelper
            DBPersistenceHelper.save_scenarios(scenarios)
        except Exception as e:
            logger.warning(f"Failed to persist scenarios to PostgreSQL: {e}")

        logger.info(f"Generated {len(scenarios)} test scenarios.")
        return scenarios

    def _try_parse_json(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(f"Could not parse LLM response as JSON: {e}")
        return []

    def _get_default_scenarios(self, has_apis: bool = True) -> List[Dict[str, Any]]:
        ui_scenarios = [
            {
                "id": "SCEN-UI-001",
                "title": "Verify User Login and Inventory Item Selection on Swag Labs (SauceDemo)",
                "description": "User logs into https://www.saucedemo.com/ using standard_user credentials, views products page, and adds Sauce Labs Backpack to shopping cart.",
                "category": "positive",
                "test_type": "UI",
                "preconditions": ["User navigates to https://www.saucedemo.com/"],
                "steps": [
                    "Navigate to https://www.saucedemo.com/",
                    "Enter Username 'standard_user'",
                    "Enter Password 'secret_sauce'",
                    "Click Login button",
                    "Verify Inventory container is visible",
                    "Click Add to Cart button for 'Sauce Labs Backpack'",
                    "Verify Shopping Cart badge shows '1'"
                ],
                "expected_result": "User successfully logs in, Inventory page loads, item is added to cart, screenshot and video recording captured.",
                "db_assertions": []
            },
            {
                "id": "SCEN-UI-002",
                "title": "Verify Login Error Message for Invalid Credentials on Swag Labs",
                "description": "User enters locked_out_user credentials and verifies error message.",
                "category": "negative",
                "test_type": "UI",
                "preconditions": ["User navigates to https://www.saucedemo.com/"],
                "steps": [
                    "Navigate to https://www.saucedemo.com/",
                    "Enter Username 'locked_out_user'",
                    "Enter Password 'secret_sauce'",
                    "Click Login button"
                ],
                "expected_result": "Error container displaying 'Epic sadface: Sorry, this user has been locked out.' is visible.",
                "db_assertions": []
            }
        ]

        if not has_apis:
            return ui_scenarios

        api_scenarios = [
            {
                "id": "SCEN-API-001",
                "title": "Verify FastAPI Endpoint POST /api/v1/claims/{id}/approve Updates PostgreSQL Claim & Payout State",
                "description": "Backend API check: approving claim CLM-1002 transitions status to APPROVED and verifies payout record creation in PostgreSQL database.",
                "category": "backend_logic",
                "test_type": "API",
                "preconditions": ["FastAPI backend active at http://localhost:8000 and PostgreSQL database initialized"],
                "steps": [
                    "Send POST request to http://localhost:8000/api/v1/claims/2/approve",
                    "Verify HTTP status code 200 OK",
                    "Query PostgreSQL database via DBAssertionHelper.assert_claim_status('CLM-1002', 'APPROVED')",
                    "Query PostgreSQL database via DBAssertionHelper.assert_payout_created('CLM-1002', 5800.50)"
                ],
                "expected_result": "HTTP 200 OK returned and PostgreSQL database verified status APPROVED with created payout record.",
                "db_assertions": [
                    "DBAssertionHelper.assert_claim_status('CLM-1002', 'APPROVED')",
                    "DBAssertionHelper.assert_payout_created('CLM-1002', 5800.50)"
                ]
            },
            {
                "id": "SCEN-API-002",
                "title": "Verify FastAPI Claims List Endpoint GET /api/v1/claims",
                "description": "Backend API check: fetch all claims from PostgreSQL database via FastAPI endpoint.",
                "category": "positive",
                "test_type": "API",
                "preconditions": ["FastAPI backend active at http://localhost:8000"],
                "steps": [
                    "Send GET request to http://localhost:8000/api/v1/claims",
                    "Verify HTTP status code 200 OK",
                    "Verify response list contains claim records"
                ],
                "expected_result": "HTTP 200 OK response with JSON list of claims.",
                "db_assertions": []
            }
        ]

        return ui_scenarios + api_scenarios
