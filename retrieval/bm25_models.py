"""Pydantic v2 models for the BM25 index layer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BM25DocumentRecord(BaseModel):
    """One tokenized document stored alongside the BM25 index.

    Stores the raw text (for debug/inspection) and the token list
    (for fast re-tokenization verification without recomputing).

    ``entity_id`` + ``offset`` allow cross-referencing with
    ``embedding_metadata.json`` and the FAISS index.
    """

    offset: int = Field(ge=0, description="Position in BM25 corpus == FAISS offset.")
    entity_id: str = Field(min_length=1)
    document: str = Field(min_length=1, description="Raw document text before tokenization.")
    tokens: list[str] = Field(description="Tokenized form used to build BM25.")


class BM25Config(BaseModel):
    """Configuration persisted alongside the BM25 index.

    Used by the loader to verify that a persisted index is compatible
    with the current catalog and tokenizer.
    """

    catalog_sha256: str = Field(
        description="SHA-256 of catalog.json at build time for stale-index detection.",
    )
    document_count: int = Field(gt=0)
    average_document_length: float = Field(ge=0.0)
    vocabulary_size: int = Field(ge=0)
    tokenizer_version: str = Field(description="Must match TOKENIZER_VERSION constant.")
    bm25_library_version: str
    created_at: datetime
