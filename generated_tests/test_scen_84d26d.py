import pytest
import requests
from database.assertions import DBAssertionHelper
import time

BASE_URL = "http://localhost:8000/api/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def test_scen_84d26d():
    """
    Successful Login
    Verify that a user can log in successfully with valid credentials.
    """
    # Step 1: Send API Request with retries
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(f"{BASE_URL}/claims/2/approve", json={}, timeout=10)
            response.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Retry {retries} in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                pytest.fail(f"Max retries exceeded: {e}")
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"