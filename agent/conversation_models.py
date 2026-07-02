"""Typed conversation state models for stateless state extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationMessage(BaseModel):
    """Single user or assistant message from a complete conversation history."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Normalize and validate message content."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("content must not be empty")
        return normalized


class ConversationState(BaseModel):
    """Structured state extracted from the complete conversation history."""

    model_config = ConfigDict(extra="forbid")

    role: str | None = None
    seniority: str | None = None
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    leadership_required: bool = False
    personality_required: bool = False
    cognitive_required: bool = False
    simulation_required: bool = False
    constraints: list[str] = Field(default_factory=list)
    mentioned_assessment_names: list[str] = Field(default_factory=list)
    comparison_requested: bool = False
    scope_flag: Literal["in_scope", "off_topic", "prompt_injection"] = "in_scope"
    conversation_goal: str | None = None
    clarification_needed: bool = False
    missing_information: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    refinement_detected: bool = False

    @field_validator(
        "technical_skills",
        "soft_skills",
        "constraints",
        "mentioned_assessment_names",
        "missing_information",
        mode="before",
    )
    @classmethod
    def default_missing_lists(cls, value: object) -> object:
        """Treat omitted or null list fields as empty lists."""
        if value is None:
            return []
        return value

    @field_validator(
        "technical_skills",
        "soft_skills",
        "constraints",
        "mentioned_assessment_names",
        "missing_information",
    )
    @classmethod
    def normalize_string_list(cls, values: list[str]) -> list[str]:
        """Trim, deduplicate, and preserve deterministic list order."""
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            item = str(value).strip()
            key = item.casefold()
            if item and key not in seen:
                normalized.append(item)
                seen.add(key)
        return normalized

    @field_validator("role", "seniority", "conversation_goal", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert blank strings to None where appropriate."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def normalize_reasoning_summary(cls, value: object) -> str:
        """Trim reasoning summary while preserving an empty string default."""
        if value is None:
            return ""
        return str(value).strip()
