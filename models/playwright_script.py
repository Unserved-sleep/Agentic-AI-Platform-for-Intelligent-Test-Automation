from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from .test_scenario import TestLevel

class PlaywrightScript(BaseModel):
    scenario_id: str = Field(..., description="The ID of the TestScenario this script implements")
    file_name: str = Field(..., description="Suggested filename for this script (e.g., 'test_claims_approval.py')")
    code: str = Field(..., description="The raw executable Python code for the Playwright test")
    test_level: TestLevel = Field(..., description="The level of the test: UI, API_CONTRACT, or API_BACKEND")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")
    
    @field_validator('code')
    @classmethod
    def clean_code_markdown(cls, v: str) -> str:
        """Strip markdown code block tags if the LLM accidentally includes them."""
        v = v.strip()
        if v.startswith("```python"):
            v = v[9:]
        elif v.startswith("```"):
            v = v[3:]
            
        if v.endswith("```"):
            v = v[:-3]
            
        return v.strip()
    
    def to_rag_json(self) -> str:
        """Serialize the output to JSON format suitable for the RAG pipeline."""
        return self.model_dump_json(indent=2)
