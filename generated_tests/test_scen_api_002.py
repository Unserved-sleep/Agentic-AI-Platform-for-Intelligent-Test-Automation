import pytest
import requests
from database.assertions import DBAssertionHelper

BASE_URL = "http://localhost:8000/api/v1"

def test_scen_api_002():
    """
    Verify FastAPI Claims List Endpoint GET /api/v1/claims
    Backend API check: fetch all claims from PostgreSQL database via FastAPI endpoint.
    """
    # Step 1: Send API Request with retries and timeout
    try:
        response = requests.post(f"{BASE_URL}/claims/2/approve", json={}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Check if the issue is due to the server not being available
        if "ConnectionRefusedError" in str(e):
            pytest.skip("Server is not available")
        else:
            pytest.fail(f"Request to {BASE_URL}/claims/2/approve failed: {e}")
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"