import pytest
from playwright import sync_request

class DocumentPage:
    pass

@pytest.fixture
def request():
    return sync_request

def test_no_file_provided(request):
    response = request.post("/api/documents")
    expect(response.status).to_equal(400)

    # Additional API specific assertions can be added here if needed
    # For instance, you can verify the response body or headers
    # expect(response.json()).to_contain({"error": "No file provided"})

    # No database assertions are needed for API CONTRACT tests