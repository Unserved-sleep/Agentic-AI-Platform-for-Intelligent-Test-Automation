import pytest
import requests
from database.assertions import DBAssertionHelper
import time

BASE_URL = "http://localhost:8000/api/v1"
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def test_scen_api_001():
    """
    Verify FastAPI Endpoint POST /api/v1/claims/{id}/approve Updates PostgreSQL Claim & Payout State
    Backend API check: approving claim CLM-1002 transitions status to APPROVED and verifies payout record creation in PostgreSQL database.
    """
    # Step 1: Send API Request with retry
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(f"{BASE_URL}/claims/2/approve", json={}, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            break
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
            if retries < MAX_RETRIES - 1:
                print(f"Request failed (attempt {retries + 1}/{MAX_RETRIES}). Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                retries += 1
            else:
                print(f"Request failed after {MAX_RETRIES} attempts. Giving up.")
                pytest.fail(f"Request failed after {MAX_RETRIES} attempts: {e}")
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"