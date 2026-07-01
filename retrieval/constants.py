"""Constants for the retrieval embedding index builder."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Filesystem paths
# ---------------------------------------------------------------------------

CANONICAL_CATALOG_PATH = Path("catalog/catalog.json")
INDEXES_DIR = Path("indexes")
FAISS_INDEX_PATH = INDEXES_DIR / "embedding.index"
METADATA_PATH = INDEXES_DIR / "embedding_metadata.json"
CONFIG_PATH = INDEXES_DIR / "embedding_config.json"

# BM25 index paths
BM25_INDEX_PATH = INDEXES_DIR / "bm25_index.pkl"
BM25_CORPUS_PATH = INDEXES_DIR / "bm25_corpus.json"
BM25_CONFIG_PATH = INDEXES_DIR / "bm25_config.json"

# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
EMBEDDING_BATCH_SIZE: int = 64

# ---------------------------------------------------------------------------
# Text document template
# ---------------------------------------------------------------------------

DOCUMENT_TEMPLATE: str = (
    "Name:\n{name}\n\n"
    "Description:\n{description}\n\n"
    "Categories:\n{categories}\n\n"
    "Job Levels:\n{job_levels}\n\n"
    "Languages:\n{languages}\n\n"
    "Duration:\n{duration}\n\n"
    "Status:\n{status}\n\n"
    "Remote:\n{remote}\n\n"
    "Adaptive:\n{adaptive}"
)
