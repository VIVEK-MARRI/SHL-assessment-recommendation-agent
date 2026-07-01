"""Integration + unit tests for retrieval.bm25_builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rank_bm25 import BM25Okapi

from retrieval.bm25_builder import BM25BuilderError, build_bm25_index_pipeline


class TestBuildBm25IndexPipeline:
    def test_missing_catalog_raises(self, tmp_path: Path):
        with pytest.raises(BM25BuilderError, match="not found"):
            build_bm25_index_pipeline(catalog_path=tmp_path / "missing.json")

    def test_empty_catalog_raises(self, tmp_path: Path):
        empty = tmp_path / "catalog.json"
        empty.write_text("[]", encoding="utf-8")
        with pytest.raises(BM25BuilderError, match="no assessments"):
            build_bm25_index_pipeline(catalog_path=empty)

    def test_full_pipeline(self, tmp_path: Path):
        """Integration: run full BM25 pipeline against the real catalog."""
        idx_p = tmp_path / "bm25_index.pkl"
        docs_p = tmp_path / "bm25_corpus.json"
        cfg_p = tmp_path / "bm25_config.json"

        build_bm25_index_pipeline(
            index_path=idx_p,
            corpus_path=docs_p,
            config_path=cfg_p,
        )

        # All three files must exist
        assert idx_p.exists(), "bm25_index.pkl not created"
        assert docs_p.exists(), "bm25_corpus.json not created"
        assert cfg_p.exists(), "bm25_config.json not created"

        # Validate documents
        docs = json.loads(docs_p.read_text(encoding="utf-8"))
        assert len(docs) > 0
        assert all(k in docs[0] for k in ("entity_id", "offset", "document", "tokens"))

        # Validate config
        cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
        assert cfg["document_count"] == len(docs)
        assert cfg["tokenizer_version"] == "1.0"
        assert len(cfg["catalog_sha256"]) == 64  # SHA-256 hex = 64 chars
        assert "average_document_length" in cfg
        assert "vocabulary_size" in cfg

        # Pickle must load as BM25Okapi
        import pickle
        loaded = pickle.loads(idx_p.read_bytes())
        assert isinstance(loaded, BM25Okapi)

    def test_corpus_ordering_matches_embedding_metadata(self):
        """BM25 document offsets must match embedding_metadata.json offsets."""
        from retrieval.bm25_loader import load_bm25_index
        from retrieval.index_loader import load_embedding_index

        bm25 = load_bm25_index(catalog_path=None)
        embedding = load_embedding_index(catalog_path=None)

        assert len(bm25.documents) == len(embedding.metadata), (
            "BM25 corpus size differs from FAISS metadata count"
        )
        for bm25_doc, emb_meta in zip(bm25.documents, embedding.metadata):
            assert bm25_doc.entity_id == emb_meta.entity_id, (
                f"Corpus ordering mismatch at offset {bm25_doc.offset}: "
                f"BM25={bm25_doc.entity_id} FAISS={emb_meta.entity_id}"
            )
