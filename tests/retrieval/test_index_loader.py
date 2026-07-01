"""Unit tests for retrieval.index_loader.load_embedding_index."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pytest

from retrieval.embedding_index import (
    build_embedding_config,
    build_faiss_index,
    build_metadata,
    persist_index,
)
from retrieval.index_loader import EmbeddingIndexLoadError, load_embedding_index
from retrieval.models import AssessmentMetadataRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_normalised(n: int = 3, dim: int = 16) -> np.ndarray:
    rng = np.random.default_rng(7)
    raw = rng.standard_normal((n, dim)).astype(np.float32)
    return raw / np.linalg.norm(raw, axis=1, keepdims=True)


def _write_valid_index(tmp_path: Path, n: int = 3, dim: int = 16):
    """Write a consistent set of index, metadata, and config files."""
    embs = _random_normalised(n, dim)
    index = build_faiss_index(embs)
    records = [
        AssessmentMetadataRecord(
            offset=i, entity_id=str(i), name=f"A{i}",
            url="https://shl.com/", test_type="K",
            keys=["Knowledge & Skills"],
            job_levels=["Graduate"],
            languages=["English (US)"],
            duration="10 minutes",
            duration_minutes=10,
            remote=True,
            adaptive=False,
        )
        for i in range(n)
    ]
    cfg = build_embedding_config(embs, "2026-01-01T00:00:00+00:00", "dummysha256", n)
    idx_p = tmp_path / "embedding.index"
    meta_p = tmp_path / "embedding_metadata.json"
    cfg_p = tmp_path / "embedding_config.json"
    persist_index(index, records, cfg, idx_p, meta_p, cfg_p)
    return idx_p, meta_p, cfg_p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadEmbeddingIndex:
    def test_successful_load(self, tmp_path: Path):
        idx_p, meta_p, cfg_p = _write_valid_index(tmp_path)
        result = load_embedding_index(idx_p, meta_p, cfg_p, catalog_path=None)
        assert result.index.ntotal == 3
        assert len(result.metadata) == 3
        assert result.config.num_assessments == 3

    def test_missing_index_file(self, tmp_path: Path):
        _, meta_p, cfg_p = _write_valid_index(tmp_path)
        with pytest.raises(EmbeddingIndexLoadError, match="not found"):
            load_embedding_index(tmp_path / "missing.index", meta_p, cfg_p, catalog_path=None)

    def test_missing_metadata_file(self, tmp_path: Path):
        idx_p, _, cfg_p = _write_valid_index(tmp_path)
        with pytest.raises(EmbeddingIndexLoadError, match="not found"):
            load_embedding_index(idx_p, tmp_path / "missing_meta.json", cfg_p, catalog_path=None)

    def test_missing_config_file(self, tmp_path: Path):
        idx_p, meta_p, _ = _write_valid_index(tmp_path)
        with pytest.raises(EmbeddingIndexLoadError, match="not found"):
            load_embedding_index(idx_p, meta_p, tmp_path / "missing_cfg.json", catalog_path=None)

    def test_corrupted_index_file(self, tmp_path: Path):
        idx_p, meta_p, cfg_p = _write_valid_index(tmp_path)
        idx_p.write_bytes(b"this is not a faiss index")
        with pytest.raises(EmbeddingIndexLoadError):
            load_embedding_index(idx_p, meta_p, cfg_p, catalog_path=None)

    def test_corrupted_metadata_json(self, tmp_path: Path):
        idx_p, meta_p, cfg_p = _write_valid_index(tmp_path)
        meta_p.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(EmbeddingIndexLoadError):
            load_embedding_index(idx_p, meta_p, cfg_p, catalog_path=None)

    def test_metadata_count_mismatch(self, tmp_path: Path):
        """If metadata has fewer records than index vectors, raise."""
        idx_p, meta_p, cfg_p = _write_valid_index(tmp_path, n=3)
        # Overwrite metadata with only 2 records
        short_meta = [
            {"offset": 0, "entity_id": "0", "name": "A0", "url": "https://shl.com/", "test_type": "K"},
            {"offset": 1, "entity_id": "1", "name": "A1", "url": "https://shl.com/", "test_type": "K"},
        ]
        meta_p.write_text(json.dumps(short_meta), encoding="utf-8")
        with pytest.raises(EmbeddingIndexLoadError, match="Consistency"):
            load_embedding_index(idx_p, meta_p, cfg_p, catalog_path=None)

    def test_loaded_metadata_fields(self, tmp_path: Path):
        idx_p, meta_p, cfg_p = _write_valid_index(tmp_path, n=2)
        result = load_embedding_index(idx_p, meta_p, cfg_p, catalog_path=None)
        r = result.metadata[0]
        assert hasattr(r, "entity_id")
        assert hasattr(r, "name")
        assert hasattr(r, "url")
        assert hasattr(r, "test_type")
        assert hasattr(r, "offset")
        # New extended fields
        assert hasattr(r, "job_levels")
        assert hasattr(r, "languages")
        assert hasattr(r, "duration")
        assert hasattr(r, "keys")

