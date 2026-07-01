from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class LLMGenerationResult(BaseModel):
    """Structured result from the Response Generation LLM."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    recommended_names: list[str] = Field(default_factory=list)
    end_of_conversation: bool = False
    
    # Metadata
    provider: str
    model: str
    latency_ms: float
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    finish_reason: str
