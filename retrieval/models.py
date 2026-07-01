"""Pydantic v2 models for the retrieval embedding layer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentMetadataRecord(BaseModel):
    """Metadata entry stored alongside the FAISS index for one assessment.

    No embedding vectors are stored here.  Fields are limited to those
    needed by downstream retrieval to identify, present, and filter results
    without re-loading the full catalog.
    """

    offset: int = Field(ge=0, description="Row index inside the FAISS index.")
    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    test_type: str = Field(default="", description="Pipe-joined type codes derived from keys.")
    keys: list[str] = Field(default_factory=list, description="Raw category keys from catalog.")
    job_levels: list[str] = Field(default_factory=list, description="Applicable job levels.")
    languages: list[str] = Field(default_factory=list, description="Available languages.")
    duration: str = Field(default="", description="Human-readable duration string.")
    duration_minutes: int | None = Field(
        default=None,
        description="Parsed numeric duration in minutes; None if untimed or unparseable.",
    )
    remote: bool = Field(default=True, description="Remotely deliverable flag.")
    adaptive: bool = Field(default=False, description="Adaptive testing flag.")


class EmbeddingConfig(BaseModel):
    """Configuration persisted alongside the FAISS index.

    Downstream loaders use this to verify that an index was built with
    compatible settings before trusting its contents.  The catalog_sha256
    fingerprint detects content changes that mtime alone cannot catch
    (e.g. file copied/touched without content modification).
    """

    embedding_model: str
    embedding_dim: int = Field(gt=0)
    catalog_version: str = Field(
        description="ISO-8601 last-modified timestamp of catalog.json.",
    )
    catalog_sha256: str = Field(
        description="SHA-256 hex digest of catalog.json at index build time.",
    )
    created_at: datetime
    num_assessments: int = Field(gt=0)
    batch_size: int = Field(gt=0)
