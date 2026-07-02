"""Builds and persists the FAISS embedding index and associated metadata."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

from retrieval.constants import (
    CONFIG_PATH,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    INDEXES_DIR,
    METADATA_PATH,
)
from retrieval.models import AssessmentMetadataRecord, EmbeddingConfig

logger = logging.getLogger(__name__)


class EmbeddingIndexError(Exception):
    """Raised when index building or persistence fails."""


def _derive_test_type(keys: list[str]) -> str:
    """Derive a pipe-joined test type code string from category keys.

    Args:
        keys: List of category strings from an assessment.

    Returns:
        Pipe-joined type codes, e.g. ``"K|P"``.  Empty string if no keys.
    """
    from catalog.constants import KEY_TO_TEST_TYPE_MAP

    codes = [KEY_TO_TEST_TYPE_MAP[k] for k in keys if k in KEY_TO_TEST_TYPE_MAP]
    return "|".join(dict.fromkeys(codes))  # preserve order, deduplicate


_DURATION_RE = re.compile(r"(\d+)")


def _parse_duration_minutes(duration: str) -> int | None:
    """Extract the first integer from a duration string.

    Args:
        duration: Human-readable duration string, e.g. ``"30 minutes"``.

    Returns:
        Integer minutes, or ``None`` if the string is empty, "Untimed",
        "Variable", or contains no numeric content.
    """
    if not duration or duration.lower() in ("untimed", "variable", "unknown"):
        return None
    match = _DURATION_RE.search(duration)
    return int(match.group(1)) if match else None


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Construct an IndexFlatIP from normalised embeddings.

    Args:
        embeddings: Float32 array of shape (n, dim) with L2-normalised rows.

    Returns:
        Populated FAISS IndexFlatIP.

    Raises:
        EmbeddingIndexError: If FAISS index creation fails.
    """
    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise EmbeddingIndexError("embeddings must be a non-empty 2-D float32 array")

    dim = embeddings.shape[1]
    logger.info("Building FAISS IndexFlatIP: dim=%d vectors=%d", dim, embeddings.shape[0])
    try:
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
    except Exception as exc:
        raise EmbeddingIndexError(f"FAISS index creation failed: {exc}") from exc

    logger.info("FAISS index built: total_vectors=%d", index.ntotal)
    return index


def persist_index(
    index: faiss.IndexFlatIP,
    metadata: list[AssessmentMetadataRecord],
    config: EmbeddingConfig,
    index_path: Path = FAISS_INDEX_PATH,
    metadata_path: Path = METADATA_PATH,
    config_path: Path = CONFIG_PATH,
) -> None:
    """Write the FAISS index, metadata, and config files to disk.

    Args:
        index: Populated FAISS index.
        metadata: One metadata record per assessment, in index order.
        config: Embedding configuration.
        index_path: Destination for the FAISS binary file.
        metadata_path: Destination for the JSON metadata file.
        config_path: Destination for the JSON config file.

    Raises:
        EmbeddingIndexError: If any write operation fails.
    """
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    # Write FAISS index
    try:
        faiss.write_index(index, str(index_path))
        logger.info("FAISS index written: path=%s", index_path)
    except Exception as exc:
        raise EmbeddingIndexError(f"Failed to write FAISS index to {index_path}: {exc}") from exc

    # Write metadata JSON
    try:
        meta_payload = [rec.model_dump() for rec in metadata]
        metadata_path.write_text(
            json.dumps(meta_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("Metadata written: path=%s records=%d", metadata_path, len(meta_payload))
    except Exception as exc:
        raise EmbeddingIndexError(
            f"Failed to write metadata to {metadata_path}: {exc}"
        ) from exc

    # Write config JSON
    try:
        config_payload = config.model_dump(mode="json")
        config_path.write_text(
            json.dumps(config_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("Config written: path=%s", config_path)
    except Exception as exc:
        raise EmbeddingIndexError(f"Failed to write config to {config_path}: {exc}") from exc


def build_metadata(assessments: list, offset_start: int = 0) -> list[AssessmentMetadataRecord]:
    """Build one metadata record per assessment.

    Args:
        assessments: Canonical Assessment objects in index order.
        offset_start: First offset value (0 for a fresh index).

    Returns:
        List of AssessmentMetadataRecord, one per assessment.
    """
    records = []
    for offset, assessment in enumerate(assessments, start=offset_start):
        records.append(
            AssessmentMetadataRecord(
                offset=offset,
                entity_id=assessment.entity_id,
                name=assessment.name,
                description=assessment.description,
                url=assessment.link,
                test_type=_derive_test_type(assessment.keys),
                keys=list(assessment.keys),
                job_levels=list(assessment.job_levels),
                languages=list(assessment.languages),
                duration=assessment.duration,
                duration_minutes=_parse_duration_minutes(assessment.duration),
                remote=assessment.remote,
                adaptive=assessment.adaptive,
            )
        )
    return records


def build_embedding_config(
    embeddings: np.ndarray,
    catalog_version: str,
    catalog_sha256: str,
    num_assessments: int,
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> EmbeddingConfig:
    """Build an EmbeddingConfig from pipeline parameters.

    Args:
        embeddings: Embedding array (used to read embedding_dim).
        catalog_version: ISO-8601 last-modified timestamp of catalog.json.
        catalog_sha256: SHA-256 hex digest of catalog.json bytes.
        num_assessments: Number of assessments indexed.
        batch_size: Batch size used during encoding.

    Returns:
        Populated EmbeddingConfig instance.
    """
    return EmbeddingConfig(
        embedding_model=EMBEDDING_MODEL_NAME,
        embedding_dim=embeddings.shape[1],
        catalog_version=catalog_version,
        catalog_sha256=catalog_sha256,
        created_at=datetime.now(tz=timezone.utc),
        num_assessments=num_assessments,
        batch_size=batch_size,
    )
