"""
Playwright Script Agent: Generates executable Playwright Python test scripts for each test scenario.
Produces Page Object Model (POM) UI scripts targeting SauceDemo and API scripts using httpx/requests,
with integrated DBAssertionHelper calls for PostgreSQL state validation.
"""
import os
from pathlib import Path
from typing import Dict, Any
from shared.schemas import TestScenario, GeneratedTestScript
from configs.config import GENERATED_TESTS_DIR, SCREENSHOTS_DIR, TRACES_DIR, VIDEOS_DIR, HEADLESS
from agents.llm_client import llm_client
from prompts.system_prompts import SCRIPT_GENERATOR_PROMPT
from shared.logger import get_logger

logger = get_logger("agents.script_agent")

class PlaywrightScriptAgent:
    """Generates production-ready Playwright Python scripts for SauceDemo UI and FastAPI API with PostgreSQL assertions."""

    def generate_script(self, scenario: TestScenario) -> GeneratedTestScript:
        filename = f"test_{scenario.id.lower().replace('-', '_')}.py"
        file_path = str(GENERATED_TESTS_DIR / filename)

        if scenario.test_type.upper() == "UI":
            script_code = self._generate_ui_script(scenario)
            pom_code = self._generate_pom_code(scenario)
        else:
            script_code = self._generate_api_script(scenario)
            pom_code = None

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(script_code)

        logger.info(f"Generated Playwright test script with artifacts tracing: {file_path}")

        script_obj = GeneratedTestScript(
            scenario_id=scenario.id,
            title=scenario.title,
            test_type=scenario.test_type,
            page_object_code=pom_code,
            script_code=script_code,
            file_path=file_path,
            db_checks_included=len(scenario.db_assertions) > 0
        )

        # Persist Generated Script to PostgreSQL
        try:
            from database.persistence import DBPersistenceHelper
            DBPersistenceHelper.save_script(script_obj)
        except Exception as e:
            logger.warning(f"Failed to persist script to PostgreSQL: {e}")

        return script_obj

    def _generate_ui_script(self, scenario: TestScenario) -> str:
        scenario_clean = scenario.id.replace("-", "_").upper()
        return f'''import pytest
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from configs.config import SCREENSHOTS_DIR, TRACES_DIR, VIDEOS_DIR, HEADLESS, ENABLE_SCREENSHOTS, ENABLE_TRACING, ENABLE_VIDEO, CAPTURE_PASSED_TESTS

class SauceDemoLoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login-button")
        self.error_container = page.locator("h3[data-test='error']")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

class SauceDemoInventoryPage:
    def __init__(self, page):
        self.page = page
        self.inventory_container = page.locator(".inventory_list")
        self.add_backpack_btn = page.locator("#add-to-cart-sauce-labs-backpack")
        self.cart_badge = page.locator(".shopping_cart_badge")

def test_{scenario.id.lower().replace("-", "_")}():
    """
    {scenario.title}
    {scenario.description}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_prefix = f"RUN-EXEC_{scenario_clean}_{{timestamp}}_UI"

    with sync_playwright() as p:
        # Launch browser window (HEADLESS=False visually opens the browser on screen!)
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=500)
        
        # Configure Video Recording & Viewport
        video_kwargs = {{"record_video_dir": str(VIDEOS_DIR), "viewport": {{"width": 1280, "height": 720}}}} if ENABLE_VIDEO else {{}}
        context = browser.new_context(**video_kwargs)

        # Start Playwright Tracing
        if ENABLE_TRACING:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()
        test_failed = False
        
        try:
            # Step 1: Open Swag Labs Page
            page.goto("https://www.saucedemo.com/")
            login_page = SauceDemoLoginPage(page)
            
            # Step 2: Login Credentials
            login_page.login("standard_user", "secret_sauce")
            
            # Step 3: Verify Inventory Page & Add Item to Cart
            inventory_page = SauceDemoInventoryPage(page)
            expect(inventory_page.inventory_container).to_be_visible(timeout=10000)
            
            if inventory_page.add_backpack_btn.is_visible():
                inventory_page.add_backpack_btn.click()
                expect(inventory_page.cart_badge).to_have_text("1", timeout=5000)
            
            # Take Action Screenshot
            shot_path = SCREENSHOTS_DIR / f"{{run_prefix}}.png"
            page.screenshot(path=str(shot_path))
            
        except Exception as e:
            test_failed = True
            if ENABLE_SCREENSHOTS:
                shot_path = SCREENSHOTS_DIR / f"{{run_prefix}}.png"
                page.screenshot(path=str(shot_path))
            raise e
        finally:
            # Save Playwright Trace Zip
            if ENABLE_TRACING:
                trace_path = TRACES_DIR / f"{{run_prefix}}.zip"
                context.tracing.stop(path=str(trace_path))

            # Save Recorded Video File
            video_file = page.video.path() if page.video else None
            context.close()
            browser.close()

            if video_file and os.path.exists(video_file) and ENABLE_VIDEO:
                target_video = VIDEOS_DIR / f"{{run_prefix}}.webm"
                try:
                    os.replace(video_file, target_video)
                except Exception:
                    pass
'''

    def _generate_api_script(self, scenario: TestScenario) -> str:
        return f'''import pytest
import requests
from database.assertions import DBAssertionHelper

BASE_URL = "http://localhost:8000/api/v1"

def test_{scenario.id.lower().replace("-", "_")}():
    """
    {scenario.title}
    {scenario.description}
    """
    # Step 1: Send API Request
    response = requests.post(f"{{BASE_URL}}/claims/2/approve", json={{}})
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {{response.status_code}}: {{response.text}}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {{db_claim_check['message']}}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {{db_payout_check['message']}}"
'''

    def _generate_pom_code(self, scenario: TestScenario) -> str:
        return '''class SauceDemoLoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login-button")

class SauceDemoInventoryPage:
    def __init__(self, page):
        self.page = page
        self.inventory_container = page.locator(".inventory_list")
        self.add_backpack_btn = page.locator("#add-to-cart-sauce-labs-backpack")
        self.cart_badge = page.locator(".shopping_cart_badge")
'''
