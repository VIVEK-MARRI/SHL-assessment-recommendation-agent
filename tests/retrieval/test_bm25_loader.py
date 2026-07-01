"""Unit tests for retrieval.bm25_loader."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest
from rank_bm25 import BM25Okapi

from retrieval.bm25_index import (
    build_bm25_config,
    build_bm25_index,
    build_document_records,
    persist_bm25_index,
)
from retrieval.bm25_loader import BM25LoadError, load_bm25_index
from retrieval.bm25_models import BM25DocumentRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_valid_bm25(tmp_path: Path, n: int = 3) -> tuple[Path, Path, Path]:
    """Write a consistent set of BM25 artifacts to tmp_path."""
    corpus = [["token", f"doc{i}"] for i in range(n)]
    index = build_bm25_index(corpus)
    records = [
        BM25DocumentRecord(
            offset=i, entity_id=str(i),
            document=f"document {i}", tokens=["token", f"doc{i}"]
        )
        for i in range(n)
    ]
    cfg = build_bm25_config("dummysha256", n, 5.0, 10)
    idx_p = tmp_path / "bm25_index.pkl"
    docs_p = tmp_path / "bm25_corpus.json"
    cfg_p = tmp_path / "bm25_config.json"
    persist_bm25_index(index, records, cfg, idx_p, docs_p, cfg_p)
    return idx_p, docs_p, cfg_p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadBm25Index:
    def test_successful_load(self, tmp_path: Path):
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        result = load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)
        assert isinstance(result.index, BM25Okapi)
        assert len(result.documents) == 3
        assert result.config.document_count == 3

    def test_missing_index_file(self, tmp_path: Path):
        _, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        with pytest.raises(BM25LoadError, match="not found"):
            load_bm25_index(tmp_path / "missing.pkl", docs_p, cfg_p, catalog_path=None)

    def test_missing_documents_file(self, tmp_path: Path):
        idx_p, _, cfg_p = _write_valid_bm25(tmp_path)
        with pytest.raises(BM25LoadError, match="not found"):
            load_bm25_index(idx_p, tmp_path / "missing.json", cfg_p, catalog_path=None)

    def test_missing_config_file(self, tmp_path: Path):
        idx_p, docs_p, _ = _write_valid_bm25(tmp_path)
        with pytest.raises(BM25LoadError, match="not found"):
            load_bm25_index(idx_p, docs_p, tmp_path / "missing_cfg.json", catalog_path=None)

    def test_corrupted_pickle(self, tmp_path: Path):
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        idx_p.write_bytes(b"not a valid pickle")
        with pytest.raises(BM25LoadError):
            load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)

    def test_corrupted_documents_json(self, tmp_path: Path):
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        docs_p.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(BM25LoadError):
            load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)

    def test_document_count_mismatch(self, tmp_path: Path):
        """Overwrite documents with fewer records than config declares."""
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path, n=3)
        short_docs = [
            {"offset": 0, "entity_id": "0", "document": "doc 0", "tokens": ["doc", "0"]},
        ]
        docs_p.write_text(json.dumps(short_docs), encoding="utf-8")
        with pytest.raises(BM25LoadError, match="Consistency"):
            load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)

    def test_tokenizer_version_mismatch(self, tmp_path: Path):
        """Manually write config with a different tokenizer version."""
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        cfg_data = json.loads(cfg_p.read_text(encoding="utf-8"))
        cfg_data["tokenizer_version"] = "0.0"
        cfg_p.write_text(json.dumps(cfg_data), encoding="utf-8")
        with pytest.raises(BM25LoadError, match="Tokenizer version mismatch"):
            load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)

    def test_sha_mismatch_warns_not_raises(self, tmp_path: Path, caplog):
        """SHA mismatch should warn but not raise."""
        import logging
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path)
        # Write a fake catalog that doesn't match the stored SHA
        fake_catalog = tmp_path / "catalog.json"
        fake_catalog.write_text('[]', encoding="utf-8")
        with caplog.at_level(logging.WARNING):
            result = load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=fake_catalog)
        assert result.index is not None
        assert any("Stale" in r.message for r in caplog.records)

    def test_loaded_document_fields(self, tmp_path: Path):
        idx_p, docs_p, cfg_p = _write_valid_bm25(tmp_path, n=2)
        result = load_bm25_index(idx_p, docs_p, cfg_p, catalog_path=None)
        r = result.documents[0]
        assert hasattr(r, "offset")
        assert hasattr(r, "entity_id")
        assert hasattr(r, "document")
        assert hasattr(r, "tokens")
