"""Unit tests for retrieval.embedding_index module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import faiss
import numpy as np
import pytest

from retrieval.embedding_index import (
    EmbeddingIndexError,
    _parse_duration_minutes,
    build_embedding_config,
    build_faiss_index,
    build_metadata,
    persist_index,
    _derive_test_type,
)
from retrieval.models import AssessmentMetadataRecord, EmbeddingConfig
from catalog.models import Assessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_assessment(entity_id: str = "1", keys: list[str] | None = None) -> Assessment:
    return Assessment.model_validate(
        dict(
            entity_id=entity_id,
            name=f"Assessment {entity_id}",
            link="https://www.shl.com/products/product-catalog/view/test/",
            description="Description.",
            keys=keys or ["Knowledge & Skills"],
            job_levels=["Graduate"],
            job_levels_raw="Graduate,",
            languages=["English (US)"],
            languages_raw="English (USA),",
            duration="30 minutes",
            duration_raw="",
            status="active",
            remote=True,
            adaptive=False,
        )
    )


def _random_embeddings(n: int = 4, dim: int = 16) -> np.ndarray:
    rng = np.random.default_rng(42)
    raw = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    return raw / norms


# ---------------------------------------------------------------------------
# _parse_duration_minutes
# ---------------------------------------------------------------------------

class TestParseDurationMinutes:
    def test_numeric(self):
        assert _parse_duration_minutes("30 minutes") == 30

    def test_untimed(self):
        assert _parse_duration_minutes("Untimed") is None

    def test_variable(self):
        assert _parse_duration_minutes("Variable") is None

    def test_empty(self):
        assert _parse_duration_minutes("") is None

    def test_max_prefix(self):
        assert _parse_duration_minutes("max 45") == 45

    def test_no_number(self):
        assert _parse_duration_minutes("unknown duration") is None


# ---------------------------------------------------------------------------
# _derive_test_type
# ---------------------------------------------------------------------------

class TestDeriveTestType:
    def test_known_key(self):
        assert _derive_test_type(["Knowledge & Skills"]) == "K"

    def test_multiple_keys(self):
        result = _derive_test_type(["Knowledge & Skills", "Simulations"])
        assert "K" in result
        assert "S" in result

    def test_unknown_key_ignored(self):
        result = _derive_test_type(["Unknown Category"])
        assert result == ""

    def test_empty_keys(self):
        assert _derive_test_type([]) == ""


# ---------------------------------------------------------------------------
# build_faiss_index
# ---------------------------------------------------------------------------

class TestBuildFaissIndex:
    def test_creates_index(self):
        embs = _random_embeddings(4, 16)
        index = build_faiss_index(embs)
        assert isinstance(index, faiss.IndexFlatIP)
        assert index.ntotal == 4
        assert index.d == 16

    def test_empty_raises(self):
        with pytest.raises(EmbeddingIndexError):
            build_faiss_index(np.empty((0, 16), dtype=np.float32))

    def test_1d_raises(self):
        with pytest.raises(EmbeddingIndexError):
            build_faiss_index(np.ones(8, dtype=np.float32))


# ---------------------------------------------------------------------------
# build_metadata
# ---------------------------------------------------------------------------

class TestBuildMetadata:
    def test_length_matches(self):
        assessments = [_make_assessment(str(i)) for i in range(5)]
        records = build_metadata(assessments)
        assert len(records) == 5

    def test_offsets_sequential(self):
        assessments = [_make_assessment(str(i)) for i in range(3)]
        records = build_metadata(assessments)
        assert [r.offset for r in records] == [0, 1, 2]

    def test_core_fields_populated(self):
        a = _make_assessment("99", keys=["Simulations"])
        records = build_metadata([a])
        r = records[0]
        assert r.entity_id == "99"
        assert r.name == "Assessment 99"
        assert r.url.startswith("https://")
        assert r.test_type == "S"

    def test_extended_fields_populated(self):
        a = _make_assessment("10")
        r = build_metadata([a])[0]
        assert r.job_levels == ["Graduate"]
        assert r.languages == ["English (US)"]
        assert r.duration == "30 minutes"
        assert r.duration_minutes == 30
        assert r.remote is True
        assert r.adaptive is False

    def test_keys_preserved(self):
        a = _make_assessment("5", keys=["Knowledge & Skills", "Simulations"])
        r = build_metadata([a])[0]
        assert "Knowledge & Skills" in r.keys
        assert "Simulations" in r.keys


# ---------------------------------------------------------------------------
# build_embedding_config
# ---------------------------------------------------------------------------

class TestBuildEmbeddingConfig:
    def test_fields(self):
        embs = _random_embeddings(3, 16)
        cfg = build_embedding_config(embs, "2026-01-01T00:00:00+00:00", "abc123", 3)
        assert cfg.embedding_dim == 16
        assert cfg.num_assessments == 3
        assert cfg.catalog_sha256 == "abc123"
        assert cfg.batch_size == 64  # default

    def test_custom_batch_size(self):
        embs = _random_embeddings(2, 8)
        cfg = build_embedding_config(embs, "v1", "deadbeef", 2, batch_size=16)
        assert cfg.batch_size == 16


# ---------------------------------------------------------------------------
# persist_index + round-trip
# ---------------------------------------------------------------------------

class TestPersistIndex:
    def _make_records(self, n: int = 2) -> list[AssessmentMetadataRecord]:
        return [
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

    def test_files_created(self, tmp_path: Path):
        embs = _random_embeddings(2, 16)
        index = build_faiss_index(embs)
        records = self._make_records(2)
        cfg = build_embedding_config(embs, "v1", "sha256abc", 2)

        idx_p = tmp_path / "embedding.index"
        meta_p = tmp_path / "embedding_metadata.json"
        cfg_p = tmp_path / "embedding_config.json"

        persist_index(index, records, cfg, idx_p, meta_p, cfg_p)

        assert idx_p.exists()
        assert meta_p.exists()
        assert cfg_p.exists()

    def test_metadata_readable(self, tmp_path: Path):
        embs = _random_embeddings(2, 16)
        index = build_faiss_index(embs)
        records = self._make_records(2)
        cfg = build_embedding_config(embs, "v1", "sha256abc", 2)

        idx_p = tmp_path / "e.index"
        meta_p = tmp_path / "meta.json"
        cfg_p = tmp_path / "cfg.json"

        persist_index(index, records, cfg, idx_p, meta_p, cfg_p)
        data = json.loads(meta_p.read_text(encoding="utf-8"))
        assert len(data) == 2
        assert data[0]["entity_id"] == "0"
        assert data[0]["duration_minutes"] == 10
        assert data[0]["remote"] is True

    def test_config_has_sha256(self, tmp_path: Path):
        embs = _random_embeddings(2, 16)
        index = build_faiss_index(embs)
        records = self._make_records(2)
        cfg = build_embedding_config(embs, "v1", "myhash123", 2)

        persist_index(index, records, cfg, tmp_path / "e.index",
                      tmp_path / "meta.json", tmp_path / "cfg.json")
        cfg_data = json.loads((tmp_path / "cfg.json").read_text(encoding="utf-8"))
        assert cfg_data["catalog_sha256"] == "myhash123"
