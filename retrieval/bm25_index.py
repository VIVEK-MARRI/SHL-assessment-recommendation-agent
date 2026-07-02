"""Builds and persists the BM25 lexical index.

Responsibilities
----------------
* Accept a corpus of tokenized documents.
* Construct ``BM25Okapi`` from ``rank_bm25``.
* Persist:
  - ``bm25_index.pkl``   — pickled BM25Okapi object.
  - ``bm25_corpus.json`` — entity_id + tokens + raw document per record.
  - ``bm25_config.json``    — SHA-256, count, tokenizer version, timestamps.
"""

from __future__ import annotations

import json
import logging
import pickle
import re
from datetime import datetime, timezone
from pathlib import Path

import rank_bm25
from rank_bm25 import BM25Okapi

from retrieval.bm25_models import BM25Config, BM25DocumentRecord
from retrieval.bm25_tokenizer import TOKENIZER_VERSION
from retrieval.constants import (
    BM25_CONFIG_PATH,
    BM25_CORPUS_PATH,
    BM25_INDEX_PATH,
    INDEXES_DIR,
)

logger = logging.getLogger(__name__)


class BM25IndexError(Exception):
    """Raised when BM25 index construction or persistence fails."""


_DURATION_RE = re.compile(r"(\d+)")


def _derive_test_type(keys: list[str]) -> str:
    """Derive a pipe-joined test type code string from category keys."""
    from catalog.constants import KEY_TO_TEST_TYPE_MAP

    codes = [KEY_TO_TEST_TYPE_MAP[k] for k in keys if k in KEY_TO_TEST_TYPE_MAP]
    return "|".join(dict.fromkeys(codes))


def _parse_duration_minutes(duration: str) -> int | None:
    """Extract the first integer minute value from a duration string."""
    if not duration or duration.lower() in ("untimed", "variable", "unknown"):
        return None
    match = _DURATION_RE.search(duration)
    return int(match.group(1)) if match else None


def build_bm25_index(token_corpus: list[list[str]]) -> BM25Okapi:
    """Construct a BM25Okapi index from a tokenized corpus.

    Args:
        token_corpus: List of token lists, one per document.  Must be
            non-empty and ordered to match FAISS ``embedding_metadata.json``.

    Returns:
        Fitted BM25Okapi instance.

    Raises:
        BM25IndexError: If the corpus is empty or construction fails.
    """
    if not token_corpus:
        raise BM25IndexError("token_corpus must not be empty")

    logger.info("Building BM25Okapi index: corpus_size=%d", len(token_corpus))
    try:
        index = BM25Okapi(token_corpus)
    except Exception as exc:
        raise BM25IndexError(f"BM25Okapi construction failed: {exc}") from exc

    avg_dl = sum(len(d) for d in token_corpus) / len(token_corpus)
    logger.info(
        "BM25 index built: documents=%d avg_doc_length=%.1f",
        len(token_corpus),
        avg_dl,
    )
    return index


def persist_bm25_index(
    index: BM25Okapi,
    documents: list[BM25DocumentRecord],
    config: BM25Config,
    index_path: Path = BM25_INDEX_PATH,
    corpus_path: Path = BM25_CORPUS_PATH,
    config_path: Path = BM25_CONFIG_PATH,
) -> None:
    """Write the BM25 index, document records, and config to disk.

    Args:
        index: Fitted BM25Okapi instance.
        documents: One record per document, in corpus order.
        config: BM25 build configuration.
        index_path: Destination for pickled BM25 object.
        corpus_path: Destination for JSON document records.
        config_path: Destination for JSON config.

    Raises:
        BM25IndexError: If any write operation fails.
    """
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    # Pickle BM25 index
    try:
        index_path.write_bytes(pickle.dumps(index, protocol=pickle.HIGHEST_PROTOCOL))
        logger.info("BM25 index pickled: path=%s bytes=%d", index_path, index_path.stat().st_size)
    except Exception as exc:
        raise BM25IndexError(f"Failed to pickle BM25 index to {index_path}: {exc}") from exc

    # Write corpus JSON
    try:
        doc_payload = [rec.model_dump() for rec in documents]
        corpus_path.write_text(
            json.dumps(doc_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("BM25 corpus written: path=%s records=%d", corpus_path, len(doc_payload))
    except Exception as exc:
        raise BM25IndexError(
            f"Failed to write BM25 corpus to {corpus_path}: {exc}"
        ) from exc

    # Write config JSON
    try:
        config_payload = config.model_dump(mode="json")
        config_path.write_text(
            json.dumps(config_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("BM25 config written: path=%s", config_path)
    except Exception as exc:
        raise BM25IndexError(f"Failed to write BM25 config to {config_path}: {exc}") from exc


def build_bm25_config(
    catalog_sha256: str,
    document_count: int,
    average_document_length: float,
    vocabulary_size: int,
) -> BM25Config:
    """Build a BM25Config instance.

    Args:
        catalog_sha256: SHA-256 hex digest of catalog.json.
        document_count: Number of documents in the corpus.
        average_document_length: Average length of a tokenized document.
        vocabulary_size: Total number of unique tokens in the corpus.

    Returns:
        Populated BM25Config.
    """
    return BM25Config(
        catalog_sha256=catalog_sha256,
        document_count=document_count,
        average_document_length=average_document_length,
        vocabulary_size=vocabulary_size,
        tokenizer_version=TOKENIZER_VERSION,
        bm25_library_version=getattr(rank_bm25, "__version__", "0.2.2"),
        created_at=datetime.now(tz=timezone.utc),
    )


def build_document_records(
    assessments: list,
    documents: list[str],
    token_corpus: list[list[str]],
) -> list[BM25DocumentRecord]:
    """Build one BM25DocumentRecord per assessment.

    Args:
        assessments: Canonical Assessment objects in corpus order.
        documents: Raw document strings in corpus order.
        token_corpus: Token lists in corpus order.

    Returns:
        List of BM25DocumentRecord, one per assessment.

    Raises:
        BM25IndexError: If lengths are inconsistent.
    """
    n = len(assessments)
    if len(documents) != n or len(token_corpus) != n:
        raise BM25IndexError(
            f"Length mismatch: assessments={n} documents={len(documents)} "
            f"token_corpus={len(token_corpus)}"
        )
    return [
        BM25DocumentRecord(
            offset=i,
            entity_id=assessments[i].entity_id,
            document=documents[i],
            tokens=token_corpus[i],
            name=assessments[i].name,
            description=assessments[i].description,
            url=assessments[i].link,
            test_type=_derive_test_type(assessments[i].keys),
            keys=list(assessments[i].keys),
            job_levels=list(assessments[i].job_levels),
            languages=list(assessments[i].languages),
            duration=assessments[i].duration,
            duration_minutes=_parse_duration_minutes(assessments[i].duration),
            remote=assessments[i].remote,
            adaptive=assessments[i].adaptive,
        )
        for i in range(n)
    ]
