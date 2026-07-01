"""Pydantic v2 models for the Comparison Pipeline output layer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ComparisonAssessment(BaseModel):
    """A fully-resolved catalog record included in a comparison."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    test_type: list[str] = Field(default_factory=list)
    description: str = ""
    job_levels: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    duration: str = ""
    remote: bool = True
    adaptive: bool = False
    keys: list[str] = Field(default_factory=list)


class ComparisonContext(BaseModel):
    """Structured result of the Comparison Pipeline, ready for the Prompt Builder."""

    model_config = ConfigDict(extra="forbid")

    matched_assessments: list[ComparisonAssessment] = Field(default_factory=list)
    unmatched_names: list[str] = Field(default_factory=list)
    comparison_possible: bool = False
    reason: str = ""
