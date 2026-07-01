"""Unit tests for retrieval.bm25_index module."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest
from rank_bm25 import BM25Okapi

from retrieval.bm25_index import (
    BM25IndexError,
    build_bm25_config,
    build_bm25_index,
    build_document_records,
    persist_bm25_index,
)
from retrieval.bm25_models import BM25DocumentRecord
from catalog.models import Assessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_assessment(entity_id: str = "1") -> Assessment:
    return Assessment.model_validate(dict(
        entity_id=entity_id,
        name=f"Assessment {entity_id}",
        link="https://www.shl.com/products/product-catalog/view/test/",
        description="A test description.",
        keys=["Knowledge & Skills"],
        job_levels=["Graduate"],
        job_levels_raw="Graduate,",
        languages=["English (US)"],
        languages_raw="English (USA),",
        duration="30 minutes",
        duration_raw="",
        status="active",
        remote=True,
        adaptive=False,
    ))


def _make_corpus(n: int = 3) -> list[list[str]]:
    return [["token", f"doc{i}", "test"] for i in range(n)]


# ---------------------------------------------------------------------------
# build_bm25_index
# ---------------------------------------------------------------------------

class TestBuildBm25Index:
    def test_creates_bm25okapi(self):
        corpus = _make_corpus(3)
        index = build_bm25_index(corpus)
        assert isinstance(index, BM25Okapi)

    def test_empty_corpus_raises(self):
        with pytest.raises(BM25IndexError):
            build_bm25_index([])

    def test_corpus_size_reflected(self):
        corpus = _make_corpus(5)
        index = build_bm25_index(corpus)
        # BM25Okapi stores corpus length in doc_len
        assert len(index.doc_len) == 5


# ---------------------------------------------------------------------------
# build_document_records
# ---------------------------------------------------------------------------

class TestBuildDocumentRecords:
    def test_length_matches(self):
        assessments = [_make_assessment(str(i)) for i in range(4)]
        docs = [f"doc {i}" for i in range(4)]
        tokens = [["doc", str(i)] for i in range(4)]
        records = build_document_records(assessments, docs, tokens)
        assert len(records) == 4

    def test_offsets_sequential(self):
        assessments = [_make_assessment(str(i)) for i in range(3)]
        docs = ["x"] * 3
        tokens = [["x"]] * 3
        records = build_document_records(assessments, docs, tokens)
        assert [r.offset for r in records] == [0, 1, 2]

    def test_entity_id_correct(self):
        assessments = [_make_assessment("42")]
        records = build_document_records(assessments, ["doc"], [["doc"]])
        assert records[0].entity_id == "42"

    def test_length_mismatch_raises(self):
        assessments = [_make_assessment("1")]
        with pytest.raises(BM25IndexError, match="Length mismatch"):
            build_document_records(assessments, ["a", "b"], [["a", "b"]])


# ---------------------------------------------------------------------------
# build_bm25_config
# ---------------------------------------------------------------------------

class TestBuildBm25Config:
    def test_fields(self):
        cfg = build_bm25_config("sha256abc", 100, 15.5, 500)
        assert cfg.catalog_sha256 == "sha256abc"
        assert cfg.document_count == 100
        assert cfg.average_document_length == 15.5
        assert cfg.vocabulary_size == 500
        assert cfg.tokenizer_version == "1.0"

    def test_has_created_at(self):
        cfg = build_bm25_config("x", 10, 5.0, 50)
        assert cfg.created_at is not None


# ---------------------------------------------------------------------------
# persist_bm25_index
# ---------------------------------------------------------------------------

class TestPersistBm25Index:
    def _make_records(self, n: int = 2) -> list[BM25DocumentRecord]:
        return [
            BM25DocumentRecord(offset=i, entity_id=str(i),
                               document=f"doc {i}", tokens=["doc", str(i)])
            for i in range(n)
        ]

    def test_files_created(self, tmp_path: Path):
        corpus = _make_corpus(2)
        index = build_bm25_index(corpus)
        records = self._make_records(2)
        cfg = build_bm25_config("sha", 2, 5.0, 10)

        persist_bm25_index(
            index, records, cfg,
            tmp_path / "bm25_index.pkl",
            tmp_path / "bm25_corpus.json",
            tmp_path / "bm25_config.json",
        )

        assert (tmp_path / "bm25_index.pkl").exists()
        assert (tmp_path / "bm25_corpus.json").exists()
        assert (tmp_path / "bm25_config.json").exists()

    def test_pickle_round_trip(self, tmp_path: Path):
        corpus = _make_corpus(2)
        index = build_bm25_index(corpus)
        records = self._make_records(2)
        cfg = build_bm25_config("sha", 2, 5.0, 10)

        pkl_p = tmp_path / "bm25_index.pkl"
        persist_bm25_index(index, records, cfg, pkl_p,
                           tmp_path / "d.json", tmp_path / "c.json")

        loaded = pickle.loads(pkl_p.read_bytes())
        assert isinstance(loaded, BM25Okapi)

    def test_documents_json_readable(self, tmp_path: Path):
        corpus = _make_corpus(2)
        index = build_bm25_index(corpus)
        records = self._make_records(2)
        cfg = build_bm25_config("sha", 2, 5.0, 10)

        docs_p = tmp_path / "docs.json"
        persist_bm25_index(index, records, cfg,
                           tmp_path / "i.pkl", docs_p, tmp_path / "c.json")

        data = json.loads(docs_p.read_text(encoding="utf-8"))
        assert len(data) == 2
        assert data[0]["entity_id"] == "0"
        assert "tokens" in data[0]
        assert "document" in data[0]

    def test_config_sha256_persisted(self, tmp_path: Path):
        corpus = _make_corpus(2)
        index = build_bm25_index(corpus)
        records = self._make_records(2)
        cfg = build_bm25_config("myhash999", 2, 5.0, 10)

        cfg_p = tmp_path / "cfg.json"
        persist_bm25_index(index, records, cfg,
                           tmp_path / "i.pkl", tmp_path / "d.json", cfg_p)

        cfg_data = json.loads(cfg_p.read_text(encoding="utf-8"))
        assert cfg_data["catalog_sha256"] == "myhash999"
