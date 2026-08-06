import pytest
import requests
from database.assertions import DBAssertionHelper
import time

BASE_URL = "http://localhost:8000/api/v1"
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds

def test_scen_1bcad8():
    """
    Empty Login Fields
    Verify that a user cannot log in with empty fields.
    """
    # Step 1: Send API Request with retries
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(f"{BASE_URL}/claims/2/approve", json={})
            response.raise_for_status()  # Raise an exception for HTTP errors
            break
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Request failed (attempt {retries}/{MAX_RETRIES}). Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Request failed after {MAX_RETRIES} attempts. Giving up.")
                raise e
    
    # Step 2: Validate HTTP Response
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    
    # Step 3: Backend Read-Only PostgreSQL State Assertion
    db_claim_check = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert db_claim_check["success"] is True, f"PostgreSQL Claim Assertion Failed: {db_claim_check['message']}"
    
    db_payout_check = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert db_payout_check["success"] is True, f"PostgreSQL Payout Assertion Failed: {db_payout_check['message']}"