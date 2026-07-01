"""Loads a persisted FAISS embedding index with consistency verification."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import NamedTuple

import faiss

from retrieval.constants import (
    CANONICAL_CATALOG_PATH,
    CONFIG_PATH,
    FAISS_INDEX_PATH,
    METADATA_PATH,
)
from retrieval.models import AssessmentMetadataRecord, EmbeddingConfig

logger = logging.getLogger(__name__)


class EmbeddingIndexLoadError(Exception):
    """Raised when the index, metadata, or config cannot be loaded or verified."""


class LoadedIndex(NamedTuple):
    """Container for the fully loaded and verified embedding index."""

    index: faiss.IndexFlatIP
    metadata: list[AssessmentMetadataRecord]
    config: EmbeddingConfig


def load_embedding_index(
    index_path: Path = FAISS_INDEX_PATH,
    metadata_path: Path = METADATA_PATH,
    config_path: Path = CONFIG_PATH,
    catalog_path: Path | None = CANONICAL_CATALOG_PATH,
) -> LoadedIndex:
    """Load and verify the persistent FAISS embedding index.

    Loads the FAISS binary, metadata JSON, and config JSON then runs
    consistency checks to ensure that index vector count matches metadata
    record count and config assertion.  Optionally checks the live catalog
    SHA-256 against the fingerprint stored in config to detect stale indexes.

    Args:
        index_path: Path to the FAISS binary file.
        metadata_path: Path to the metadata JSON file.
        config_path: Path to the config JSON file.
        catalog_path: Path to the live canonical catalog for staleness check.
            Pass ``None`` to skip the SHA-256 check.

    Returns:
        LoadedIndex named tuple containing the index, metadata, and config.

    Raises:
        EmbeddingIndexLoadError: If any file is missing, corrupted, or
            internally inconsistent.
    """
    # --- Load FAISS index ---
    if not index_path.exists():
        raise EmbeddingIndexLoadError(f"FAISS index file not found: {index_path}")
    try:
        index = faiss.read_index(str(index_path))
    except Exception as exc:
        raise EmbeddingIndexLoadError(
            f"Failed to read FAISS index from {index_path}: {exc}"
        ) from exc
    logger.info("FAISS index loaded: path=%s ntotal=%d", index_path, index.ntotal)

    # --- Load metadata ---
    if not metadata_path.exists():
        raise EmbeddingIndexLoadError(f"Metadata file not found: {metadata_path}")
    try:
        raw_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata = [AssessmentMetadataRecord.model_validate(rec) for rec in raw_meta]
    except Exception as exc:
        raise EmbeddingIndexLoadError(
            f"Failed to parse metadata from {metadata_path}: {exc}"
        ) from exc
    logger.info("Metadata loaded: records=%d", len(metadata))

    # --- Load config ---
    if not config_path.exists():
        raise EmbeddingIndexLoadError(f"Config file not found: {config_path}")
    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
        config = EmbeddingConfig.model_validate(raw_config)
    except Exception as exc:
        raise EmbeddingIndexLoadError(
            f"Failed to parse config from {config_path}: {exc}"
        ) from exc
    logger.info("Config loaded: model=%s dim=%d", config.embedding_model, config.embedding_dim)

    # --- Consistency checks ---
    if index.ntotal != len(metadata):
        raise EmbeddingIndexLoadError(
            f"Consistency failure: FAISS index has {index.ntotal} vectors "
            f"but metadata has {len(metadata)} records."
        )
    if index.ntotal != config.num_assessments:
        raise EmbeddingIndexLoadError(
            f"Consistency failure: FAISS index has {index.ntotal} vectors "
            f"but config declares {config.num_assessments} assessments."
        )
    if index.d != config.embedding_dim:
        raise EmbeddingIndexLoadError(
            f"Consistency failure: FAISS index dimension {index.d} "
            f"does not match config embedding_dim {config.embedding_dim}."
        )

    # --- Staleness check (SHA-256 fingerprint) ---
    if catalog_path is not None and Path(catalog_path).exists():
        live_sha256 = hashlib.sha256(Path(catalog_path).read_bytes()).hexdigest()
        if live_sha256 != config.catalog_sha256:
            logger.warning(
                "Stale index detected: catalog SHA-256 has changed since index was built. "
                "Run scripts/build_embedding_index.py to rebuild. "
                "index_sha256=%s live_sha256=%s",
                config.catalog_sha256,
                live_sha256,
            )

    logger.info(
        "Embedding index verified: assessments=%d dim=%d",
        config.num_assessments,
        config.embedding_dim,
    )
    return LoadedIndex(index=index, metadata=metadata, config=config)
