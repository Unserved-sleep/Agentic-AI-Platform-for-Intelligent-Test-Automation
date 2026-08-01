def enrich_metadata(domain_filters: list = None) -> dict:
    return {
        "domain": domain_filters if domain_filters else ["general"],
        "environment": "staging",
        "test_type": "api_test"
    }

def build_memory_block() -> dict:
    return {
        "recent_failures": [],
        "guidelines": "Always include positive and negative test cases. Assert on HTTP status and DB state."
    }
