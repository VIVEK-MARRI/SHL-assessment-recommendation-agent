from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class ValidatedGenerationResult(BaseModel):
    """The final validated response before it reaches the Response Builder."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    validated_names: list[str] = Field(default_factory=list)
    invalid_names: list[str] = Field(default_factory=list)
    end_of_conversation: bool = False
    validation_passed: bool
    validation_errors: list[str] = Field(default_factory=list)
