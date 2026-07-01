"""Integration + unit tests for retrieval.index_builder.build_embedding_index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from retrieval.index_builder import IndexBuilderError, build_embedding_index


class TestBuildEmbeddingIndex:
    def test_missing_catalog_raises(self, tmp_path: Path):
        fake_path = tmp_path / "nonexistent_catalog.json"
        with pytest.raises(IndexBuilderError, match="not found"):
            build_embedding_index(catalog_path=fake_path)

    def test_empty_catalog_raises(self, tmp_path: Path):
        empty_catalog = tmp_path / "catalog.json"
        empty_catalog.write_text("[]", encoding="utf-8")
        with pytest.raises(IndexBuilderError, match="no assessments"):
            build_embedding_index(catalog_path=empty_catalog)

    def test_full_pipeline(self, tmp_path: Path):
        """Integration test: run the full pipeline writing to tmp_path."""
        idx_p = tmp_path / "embedding.index"
        meta_p = tmp_path / "embedding_metadata.json"
        cfg_p = tmp_path / "embedding_config.json"

        build_embedding_index(index_path=idx_p, metadata_path=meta_p, config_path=cfg_p)

        assert idx_p.exists(), "FAISS index file not created"
        assert meta_p.exists(), "Metadata file not created"
        assert cfg_p.exists(), "Config file not created"

        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        assert len(meta) > 0
        assert all(k in meta[0] for k in ("entity_id", "name", "url", "test_type", "offset"))

        cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
        assert cfg["num_assessments"] == len(meta)
        assert cfg["embedding_dim"] > 0
