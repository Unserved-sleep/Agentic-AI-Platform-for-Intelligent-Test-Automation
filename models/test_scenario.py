from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TestLevel(str, Enum):
    UI = "UI"
    API_CONTRACT = "API Contract"
    API_BACKEND = "API Backend"

class TestCategory(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    BOUNDARY = "Boundary"
    ACCESSIBILITY = "Accessibility"
    SECURITY = "Security"
    PERFORMANCE = "Performance"

class TestSubcategory(str, Enum):
    # Positive
    HAPPY_PATH = "Happy Path"
    ALTERNATE_FLOW = "Alternate Flow"
    ROLE_BASED = "Role Based"
    
    # Negative
    INVALID_INPUT = "Invalid Input"
    MISSING_INPUT = "Missing Input"
    INVALID_STATE = "Invalid State"
    
    # Boundary
    MINIMUM_VALUE = "Minimum Value"
    MAXIMUM_VALUE = "Maximum Value"
    LENGTH = "Length"
    NUMERIC_RANGE = "Numeric Range"
    
    # Accessibility
    KEYBOARD = "Keyboard"
    SCREEN_READER = "Screen Reader"
    FOCUS = "Focus"
    
    # Security
    SQL_INJECTION = "SQL Injection"
    XSS = "XSS"
    CSRF = "CSRF"
    AUTHENTICATION = "Authentication"
    AUTHORIZATION = "Authorization"
    SESSION = "Session"
    
    # Performance
    LOAD = "Load"
    STRESS = "Stress"

class TestPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestScenario(BaseModel):
    id: str = Field(..., description="Unique identifier for the test scenario (e.g., TS-001)")
    title: str = Field(..., description="A concise, descriptive title for the test scenario")
    category: TestCategory = Field(..., description="The high-level category of the test (Positive, Negative, etc.)")
    subcategory: TestSubcategory = Field(..., description="The subcategory corresponding to the test type")
    priority: TestPriority = Field(..., description="The execution priority of the test")
    description: str = Field(..., description="Detailed description of what the test verifies")
    pre_conditions: List[str] = Field(default_factory=list, description="List of pre-conditions that must be met before executing the test")
    steps: List[str] = Field(..., description="Ordered list of steps to execute the test")
    expected_result: str = Field(..., description="The expected outcome after executing the steps")
    test_level: TestLevel = Field(..., description="Whether this is a UI test, an API Contract test, or an API Backend logic test")


class ScenarioGenerationResult(BaseModel):
    requirement_id: Optional[str] = Field(default=None, description="ID of the source requirement for RAG tracking")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")
    scenarios: List[TestScenario] = Field(description="The list of generated test scenarios")
    
    def to_rag_json(self) -> str:
        """Serialize the output to JSON format suitable for Engineer 1's RAG pipeline."""
        return self.model_dump_json(indent=2)
