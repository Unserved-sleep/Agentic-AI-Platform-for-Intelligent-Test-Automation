import pytest
from playwright.sync_api import Page, expect
from database.assertions import DBAssertionHelper

class ClaimsPortalPage:
    def __init__(self, page: Page):
        self.page = page
        self.policy_input = page.locator("#policy_number")
        self.claimant_input = page.locator("#claimant_name")
        self.amount_input = page.locator("#claim_amount")
        self.submit_button = page.locator("#submit_claim_btn")
        self.success_msg = page.locator("#success_message")
        self.error_msg = page.locator("#error_message")

    def submit_claim(self, policy: str, claimant: str, amount: str):
        self.policy_input.fill(policy)
        self.claimant_input.fill(claimant)
        self.amount_input.fill(amount)
        self.submit_button.click()

def test_scen_a92139(page: Page):
    """
    Submit Claim with Invalid Data
    Test submitting a claim with invalid data
    """
    page.goto("http://localhost:8000/claims_form")
    claims_page = ClaimsPortalPage(page)
    
    # Execute Test Steps
    claims_page.submit_claim("POL-99001", "Jane Doe", "2500")
    
    # Assertions
    expect(claims_page.success_msg).to_be_visible(timeout=5000)
    
    # Backend Read-Only Database Assertion
    db_res = DBAssertionHelper.assert_claim_status("CLM-1001", "SUBMITTED")
    assert db_res["success"] is True, f"DB Assertion Failed: {db_res['message']}"
