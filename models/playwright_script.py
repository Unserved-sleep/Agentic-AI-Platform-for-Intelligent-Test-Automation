from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PlaywrightScript(BaseModel):
    scenario_id: str = Field(..., description="The ID of the TestScenario this script implements")
    file_name: str = Field(..., description="Suggested filename for this script (e.g., 'test_claims_approval.py')")
    code: str = Field(..., description="The raw executable Python code for the Playwright test")
    is_api: bool = Field(..., description="True if this uses APIRequestContext for backend testing, False if UI testing")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")
    
    def to_rag_json(self) -> str:
        """Serialize the output to JSON format suitable for the RAG pipeline."""
        return self.model_dump_json(indent=2)
