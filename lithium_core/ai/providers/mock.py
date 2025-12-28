from .base import AIProvider, AIResult
from typing import Any, Optional

class MockAIProvider(AIProvider):
    async def classify(self, text: str, context: Optional[dict[str, Any]] = None) -> AIResult:
        # Simple deterministic mock
        score = 0.1
        if "bad" in text.lower():
            score = 0.8
        
        return AIResult(
            score=score,
            label="toxic" if score > 0.5 else "clean",
            metadata={"provider": "mock"}
        )

    async def summarize(self, text: str) -> str:
        return f"Summary: {text[:50]}..."
