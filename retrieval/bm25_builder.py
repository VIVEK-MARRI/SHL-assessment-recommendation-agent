"""Orchestrates the complete BM25 index build pipeline.

Pipeline
--------
catalog/catalog.json
        ↓
    Load Assessments         (catalog package)
        ↓
    Build Text Documents     (retrieval.text_builder — same as embedding index)
        ↓
    Tokenize Documents       (retrieval.bm25_tokenizer)
        ↓
    Build BM25Okapi          (retrieval.bm25_index)
        ↓
    Build Document Records   (retrieval.bm25_index)
        ↓
    Build Config             (retrieval.bm25_index)
        ↓
    Persist                  (retrieval.bm25_index)
        ↓
indexes/bm25_index.pkl
indexes/bm25_corpus.json
indexes/bm25_config.json

Corpus Ordering Guarantee
-------------------------
The catalog is loaded via ``load_canonical_catalog()``, which returns
assessments in the SAME deterministic sort order (name, entity_id) used
by the embedding index builder.  Document ``i`` in the BM25 corpus
therefore corresponds to vector ``i`` in the FAISS index, satisfying the
hard ordering requirement for Hybrid Retrieval / RRF.
"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

from catalog import load_canonical_catalog
from retrieval.bm25_index import (
    build_bm25_config,
    build_bm25_index,
    build_document_records,
    persist_bm25_index,
)
from retrieval.bm25_tokenizer import tokenize
from retrieval.constants import (
    BM25_CONFIG_PATH,
    BM25_CORPUS_PATH,
    BM25_INDEX_PATH,
    CANONICAL_CATALOG_PATH,
)
from retrieval.text_builder import build_document

logger = logging.getLogger(__name__)


class BM25BuilderError(Exception):
    """Raised when the end-to-end BM25 build pipeline fails."""


def build_bm25_index_pipeline(
    catalog_path: Path = CANONICAL_CATALOG_PATH,
    index_path: Path = BM25_INDEX_PATH,
    corpus_path: Path = BM25_CORPUS_PATH,
    config_path: Path = BM25_CONFIG_PATH,
) -> None:
    """Execute the full BM25 index build pipeline.

    Loads the canonical catalog, builds text documents (reusing the same
    function as the embedding index), tokenizes them, constructs a
    BM25Okapi index, and persists all three artifacts.

    The corpus is produced in the same deterministic order as the FAISS
    embedding index so that document ``i`` in BM25 == vector ``i`` in FAISS.

    Args:
        catalog_path: Path to the canonical catalog JSON file.
        index_path: Destination for the pickled BM25Okapi.
        corpus_path: Destination for the JSON document records.
        config_path: Destination for the JSON config.

    Raises:
        BM25BuilderError: If the catalog is missing, empty, or any
            pipeline stage fails.
    """
    started = time.perf_counter()
    logger.info("BM25 index build started: catalog=%s", catalog_path)

    # 1. Load assessments
    if not Path(catalog_path).exists():
        raise BM25BuilderError(f"Catalog file not found: {catalog_path}")
    try:
        assessments = load_canonical_catalog(catalog_path)
    except Exception as exc:
        raise BM25BuilderError(
            f"Failed to load catalog from {catalog_path}: {exc}"
        ) from exc

    if not assessments:
        raise BM25BuilderError(f"Catalog at {catalog_path} contains no assessments.")
    logger.info("Catalog loaded: %d assessments", len(assessments))

    # 2. Build text documents — reuse text_builder (keeps BM25 + FAISS aligned)
    documents = [build_document(a) for a in assessments]
    logger.info("Text documents built: %d", len(documents))

    # 3. Tokenize
    token_corpus = [tokenize(doc) for doc in documents]
    total_tokens = sum(len(t) for t in token_corpus)
    avg_dl = total_tokens / len(token_corpus)
    logger.info(
        "Tokenization complete: total_tokens=%d avg_doc_length=%.1f",
        total_tokens,
        avg_dl,
    )

    # 4. Compute catalog SHA-256
    catalog_sha256 = hashlib.sha256(Path(catalog_path).read_bytes()).hexdigest()

    # 5. Build BM25 index
    index = build_bm25_index(token_corpus)

    # 6. Build document records and config
    document_records = build_document_records(assessments, documents, token_corpus)
    unique_tokens = set()
    for tokens in token_corpus:
        unique_tokens.update(tokens)
        
    config = build_bm25_config(
        catalog_sha256=catalog_sha256,
        document_count=len(assessments),
        average_document_length=avg_dl,
        vocabulary_size=len(unique_tokens),
    )

    # 7. Persist
    persist_bm25_index(index, document_records, config, index_path, corpus_path, config_path)

    elapsed = round(time.perf_counter() - started, 3)
    logger.info(
        "BM25 index build complete: assessments=%d avg_doc_length=%.1f elapsed=%.3fs",
        len(assessments),
        avg_dl,
        elapsed,
    )
