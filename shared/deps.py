from dataclasses import dataclass
from typing import Any

@dataclass
class AgentDeps:
    """Shared dependencies injected into PydanticAI agents."""
    rag_retriever: Any = None
    db_context_path: str = None
