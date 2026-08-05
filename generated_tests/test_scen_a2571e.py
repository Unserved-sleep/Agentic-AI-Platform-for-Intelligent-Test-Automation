import pytest
import requests
from database.assertions import DBAssertionHelper

BASE_URL = "http://localhost:8000/api/v1"

def test_scen_a2571e():
    """
    Get Claims
    Get a list of claims and verify the response is successful
    """
    # Step 1: Send API Request with retry
    import time
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(f"{BASE_URL}/claims/2/approve", json={}, timeout=10)
            response.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retries += 1
            if retries < max_retries:
                print(f"Connection error, retrying in 2 seconds... ({retries}/{max_retries})")
                time.sleep(2)
            else:
                print(f"Max retries exceeded, failing test.")
                pytest.fail(f"Failed to connect to {BASE_URL} after {max_retries} retries.")
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"