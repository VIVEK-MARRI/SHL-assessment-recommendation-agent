"""Orchestrates the complete embedding index build pipeline.

Pipeline
--------
catalog/catalog.json
        ↓
    Load Assessments          (catalog package)
        ↓
    Build Text Documents      (retrieval.text_builder)
        ↓
    Generate Embeddings       (retrieval.embedding_generator)
        ↓
    Build FAISS Index         (retrieval.embedding_index)
        ↓
    Build Metadata + Config   (retrieval.embedding_index)
        ↓
    Persist Index             (retrieval.embedding_index)
        ↓
indexes/embedding.index
indexes/embedding_metadata.json
indexes/embedding_config.json
"""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from catalog import load_canonical_catalog
from catalog.constants import CANONICAL_CATALOG_DEFAULT_PATH
from retrieval.constants import (
    CANONICAL_CATALOG_PATH,
    CONFIG_PATH,
    EMBEDDING_BATCH_SIZE,
    FAISS_INDEX_PATH,
    METADATA_PATH,
)
from retrieval.embedding_generator import generate_embeddings
from retrieval.embedding_index import (
    build_embedding_config,
    build_faiss_index,
    build_metadata,
    persist_index,
)
from retrieval.text_builder import build_document

logger = logging.getLogger(__name__)


class IndexBuilderError(Exception):
    """Raised when the end-to-end index build pipeline fails."""


def build_embedding_index(
    catalog_path: Path = CANONICAL_CATALOG_PATH,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    index_path: Path = FAISS_INDEX_PATH,
    metadata_path: Path = METADATA_PATH,
    config_path: Path = CONFIG_PATH,
) -> None:
    """Execute the full embedding index build pipeline.

    Loads the canonical catalog, converts assessments to text documents,
    generates normalised embeddings, builds a FAISS IndexFlatIP, and
    writes all three output files (index, metadata, config) to disk.

    Args:
        catalog_path: Path to the canonical catalog JSON file.
        batch_size: Encoding batch size for the embedding model.
        index_path: Destination path for the FAISS binary file.
        metadata_path: Destination path for the metadata JSON file.
        config_path: Destination path for the config JSON file.

    Raises:
        IndexBuilderError: If the catalog is missing, empty, or any
            pipeline stage fails.
    """
    started = time.perf_counter()
    logger.info("Embedding index build started: catalog=%s", catalog_path)

    # 1. Load assessments from canonical catalog
    if not Path(catalog_path).exists():
        raise IndexBuilderError(f"Catalog file not found: {catalog_path}")
    try:
        assessments = load_canonical_catalog(catalog_path)
    except Exception as exc:
        raise IndexBuilderError(f"Failed to load catalog from {catalog_path}: {exc}") from exc

    if not assessments:
        raise IndexBuilderError(f"Catalog at {catalog_path} contains no assessments.")

    logger.info("Catalog loaded: %d assessments", len(assessments))

    # 2. Build text documents
    documents = [build_document(a) for a in assessments]
    logger.info("Text documents built: %d", len(documents))

    # 3. Generate embeddings
    embeddings = generate_embeddings(documents, batch_size=batch_size)
    logger.info("Embeddings generated: shape=%s", embeddings.shape)

    # 4. Build FAISS index
    index = build_faiss_index(embeddings)

    # 5. Build metadata and config
    metadata_records = build_metadata(assessments)
    catalog_bytes = Path(catalog_path).read_bytes()
    catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()
    catalog_version = datetime.fromtimestamp(
        Path(catalog_path).stat().st_mtime,
        tz=timezone.utc,
    ).isoformat()
    config = build_embedding_config(
        embeddings=embeddings,
        catalog_version=catalog_version,
        catalog_sha256=catalog_sha256,
        num_assessments=len(assessments),
        batch_size=batch_size,
    )

    # 6. Persist everything
    persist_index(index, metadata_records, config, index_path, metadata_path, config_path)

    elapsed = round(time.perf_counter() - started, 3)
    logger.info(
        "Embedding index build complete: assessments=%d dim=%d elapsed=%.3fs",
        len(assessments),
        embeddings.shape[1],
        elapsed,
    )
