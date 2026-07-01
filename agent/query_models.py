"""Pydantic v2 models for the Query Builder output layer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QueryFilters(BaseModel):
    """Structured filters to narrow retrieval results."""

    model_config = ConfigDict(extra="forbid")

    job_levels: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    maximum_duration_minutes: int | None = None
    remote_only: bool | None = None
    adaptive_only: bool | None = None
    test_types: list[str] = Field(default_factory=list)


class RetrievalQuery(BaseModel):
    """Optimised retrieval query produced by the Query Builder."""

    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1)
    query_tokens: list[str] = Field(default_factory=list)
    required_terms: list[str] = Field(default_factory=list)
    optional_terms: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    filters: QueryFilters = Field(default_factory=QueryFilters)
    expansion_terms: list[str] = Field(default_factory=list)
