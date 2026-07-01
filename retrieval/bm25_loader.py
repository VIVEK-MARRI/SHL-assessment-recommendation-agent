"""Loads a persisted BM25 index with consistency verification."""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import NamedTuple

from rank_bm25 import BM25Okapi

from retrieval.bm25_models import BM25Config, BM25DocumentRecord
from retrieval.bm25_tokenizer import TOKENIZER_VERSION
from retrieval.constants import (
    BM25_CONFIG_PATH,
    BM25_CORPUS_PATH,
    BM25_INDEX_PATH,
    CANONICAL_CATALOG_PATH,
)

logger = logging.getLogger(__name__)


class BM25LoadError(Exception):
    """Raised when the BM25 index, documents, or config cannot be loaded."""


class LoadedBM25Index(NamedTuple):
    """Container for the fully loaded and verified BM25 index."""

    index: BM25Okapi
    documents: list[BM25DocumentRecord]
    config: BM25Config


def load_bm25_index(
    index_path: Path = BM25_INDEX_PATH,
    corpus_path: Path = BM25_CORPUS_PATH,
    config_path: Path = BM25_CONFIG_PATH,
    catalog_path: Path | None = CANONICAL_CATALOG_PATH,
) -> LoadedBM25Index:
    """Load and verify the persisted BM25 index.

    Loads the pickled BM25Okapi, JSON corpus, and JSON config then runs
    consistency checks:

    * Document count matches config ``document_count``.
    * Tokenizer version matches ``TOKENIZER_VERSION`` constant.
    * Optionally verifies catalog SHA-256 against the live catalog.

    Args:
        index_path: Path to the pickled BM25Okapi file.
        corpus_path: Path to the JSON document records file.
        config_path: Path to the JSON config file.
        catalog_path: Path to the live catalog for SHA-256 staleness check.
            Pass ``None`` to skip.

    Returns:
        LoadedBM25Index named tuple.

    Raises:
        BM25LoadError: If any file is missing, corrupted, or inconsistent.
    """
    # --- Load config first (smallest, fastest; sets expectations) ---
    if not config_path.exists():
        raise BM25LoadError(f"BM25 config file not found: {config_path}")
    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
        config = BM25Config.model_validate(raw_config)
    except Exception as exc:
        raise BM25LoadError(f"Failed to parse BM25 config from {config_path}: {exc}") from exc
    logger.info(
        "BM25 config loaded: documents=%d tokenizer=%s",
        config.document_count,
        config.tokenizer_version,
    )

    # --- Tokenizer version check ---
    if config.tokenizer_version != TOKENIZER_VERSION:
        raise BM25LoadError(
            f"Tokenizer version mismatch: index was built with "
            f"'{config.tokenizer_version}' but current version is '{TOKENIZER_VERSION}'. "
            f"Rebuild the index with scripts/build_bm25_index.py."
        )

    # --- Load pickled BM25 index ---
    if not index_path.exists():
        raise BM25LoadError(f"BM25 index file not found: {index_path}")
    try:
        index = pickle.loads(index_path.read_bytes())  # noqa: S301
    except Exception as exc:
        raise BM25LoadError(f"Failed to unpickle BM25 index from {index_path}: {exc}") from exc
    if not isinstance(index, BM25Okapi):
        raise BM25LoadError(
            f"Pickled object is {type(index).__name__}, expected BM25Okapi."
        )
    logger.info("BM25 index loaded: corpus_doc_count=%d", len(index.doc_len))

    # --- Load documents ---
    if not corpus_path.exists():
        raise BM25LoadError(f"BM25 corpus file not found: {corpus_path}")
    try:
        raw_docs = json.loads(corpus_path.read_text(encoding="utf-8"))
        documents = [BM25DocumentRecord.model_validate(rec) for rec in raw_docs]
    except Exception as exc:
        raise BM25LoadError(
            f"Failed to parse BM25 corpus from {corpus_path}: {exc}"
        ) from exc
    logger.info("BM25 corpus loaded: records=%d", len(documents))

    # --- Consistency: document count ---
    if len(documents) != config.document_count:
        raise BM25LoadError(
            f"Consistency failure: BM25 corpus file has {len(documents)} records "
            f"but config declares {config.document_count}."
        )

    # --- Staleness: catalog SHA-256 ---
    if catalog_path is not None and Path(catalog_path).exists():
        live_sha256 = hashlib.sha256(Path(catalog_path).read_bytes()).hexdigest()
        if live_sha256 != config.catalog_sha256:
            logger.warning(
                "Stale BM25 index: catalog SHA-256 has changed since index was built. "
                "Run scripts/build_bm25_index.py to rebuild. "
                "index_sha256=%s live_sha256=%s",
                config.catalog_sha256,
                live_sha256,
            )

    logger.info(
        "BM25 index verified: documents=%d tokenizer_version=%s",
        config.document_count,
        config.tokenizer_version,
    )
    return LoadedBM25Index(index=index, documents=documents, config=config)
