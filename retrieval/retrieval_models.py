"""Typed models for retrieval results and health checks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievedAssessment(BaseModel):
    """Ranked retrieval candidate resolved from persisted index metadata."""

    retrieval_source: str = "embedding"
    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    test_type: str = ""
    score: float
    rank: int = Field(ge=1)
    embedding_rank: int | None = Field(default=None, ge=1)
    bm25_rank: int | None = Field(default=None, ge=1)
    job_levels: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    duration: str = ""
    duration_minutes: int | None = None
    remote: bool = True
    adaptive: bool = False
    keys: list[str] = Field(default_factory=list)


class EmbeddingRetrieverHealth(BaseModel):
    """Runtime health details for the semantic embedding retriever."""

    model_config = ConfigDict(protected_namespaces=())

    index_loaded: bool
    model_loaded: bool
    metadata_loaded: bool
    model_name: str | None = None
    embedding_dimension: int | None = None
    number_of_indexed_assessments: int = 0
    catalog_sha: str | None = None
    average_query_latency_ms: float | None = None


class BM25RetrieverHealth(BaseModel):
    """Runtime health details for the lexical BM25 retriever."""

    bm25_loaded: bool
    corpus_loaded: bool
    document_count: int = 0
    tokenizer_version: str | None = None
    catalog_sha256: str | None = None
    average_query_latency_ms: float | None = None
