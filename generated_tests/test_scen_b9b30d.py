import pytest
import requests
from database.assertions import DBAssertionHelper

BASE_URL = "http://localhost:8000/api/v1"

def test_scen_b9b30d():
    """
    Security Check
    Verify that the website is secure and does not have any major security vulnerabilities.
    """
    # Step 1: Send API Request
    response = requests.post(f"{BASE_URL}/claims/2/approve", json={})
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"
