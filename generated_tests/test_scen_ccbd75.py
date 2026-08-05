import pytest
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

def test_scen_ccbd75():
    """
    Security Check - Claim Form
    Test the security of the claim form
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_prefix = f"RUN-EXEC_SCEN_CCBD75_{timestamp}_UI"

    with sync_playwright() as p:
        # Launch browser window (HEADLESS=False visually opens the browser on screen!)
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=500)
        
        # Configure Video Recording & Viewport
        video_kwargs = {"record_video_dir": str(VIDEOS_DIR), "viewport": {"width": 1280, "height": 720}} if ENABLE_VIDEO else {}
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
            shot_path = SCREENSHOTS_DIR / f"{run_prefix}.png"
            page.screenshot(path=str(shot_path))
            
        except Exception as e:
            test_failed = True
            if ENABLE_SCREENSHOTS:
                shot_path = SCREENSHOTS_DIR / f"{run_prefix}.png"
                page.screenshot(path=str(shot_path))
            raise e
        finally:
            # Save Playwright Trace Zip
            if ENABLE_TRACING:
                trace_path = TRACES_DIR / f"{run_prefix}.zip"
                context.tracing.stop(path=str(trace_path))

            # Save Recorded Video File
            video_file = page.video.path() if page.video else None
            context.close()
            browser.close()

            if video_file and os.path.exists(video_file) and ENABLE_VIDEO:
                target_video = VIDEOS_DIR / f"{run_prefix}.webm"
                try:
                    os.replace(video_file, target_video)
                except Exception:
                    pass
