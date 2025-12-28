from typing import Protocol, dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AIResult:
    score: float
    label: str
    metadata: dict[str, Any]

class AIProvider(Protocol):
    async def classify(self, text: str, context: Optional[dict[str, Any]] = None) -> AIResult:
        ...
        
    async def summarize(self, text: str) -> str:
        ...
