import pytest
import requests
from database.assertions import DBAssertionHelper

BASE_URL = "http://localhost:8000/api/v1"

def test_scen_5aa1e8():
    """
    Get All Claims
    Test getting all claims
    """
    # Step 1: Send API Request
    response = requests.post(f"{BASE_URL}/claims/2/approve", json={})
    
    # Step 2: Validate HTTP Response
    assert response.status_code in [200, 201], f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"
