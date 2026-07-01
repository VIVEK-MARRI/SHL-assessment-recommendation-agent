"""Unit tests for retrieval.embedding_retriever."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pytest

from retrieval.embedding_index import build_embedding_config, persist_index
from retrieval.embedding_retriever import EmbeddingRetriever, EmbeddingRetrieverError
from retrieval.models import AssessmentMetadataRecord


class FakeModel:
    """Small deterministic embedding model double."""

    def __init__(self, dim: int = 3) -> None:
        self.dim = dim
        self.calls: list[list[str]] = []

    def encode(
        self,
        documents: list[str],
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
        convert_to_numpy: bool,
    ) -> np.ndarray:
        self.calls.append(documents)
        vectors: list[np.ndarray] = []
        for document in documents:
            if "unicode" in document.lower() or "ｕｎｉｃｏｄｅ" in document.lower():
                vector = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            elif "large" in document.lower():
                vector = np.array([0.8, 0.6, 0.0], dtype=np.float32)
            else:
                vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            vectors.append(vector[: self.dim])
        output = np.vstack(vectors).astype(np.float32)
        if normalize_embeddings:
            output = output / np.linalg.norm(output, axis=1, keepdims=True)
        return output


def _metadata(n: int) -> list[AssessmentMetadataRecord]:
    return [
        AssessmentMetadataRecord(
            offset=i,
            entity_id=f"id-{i}",
            name=f"Assessment {i}",
            url=f"https://www.shl.com/{i}",
            test_type="K",
            keys=["Knowledge & Skills"],
            job_levels=["Graduate"],
            languages=["English"],
            duration="10 minutes",
            duration_minutes=10,
            remote=True,
            adaptive=False,
        )
        for i in range(n)
    ]


def _write_index(tmp_path: Path, *, n: int = 3, dim: int = 3) -> tuple[Path, Path, Path]:
    vectors = np.eye(dim, dtype=np.float32)[:n]
    if n > dim:
        extra = np.tile(np.array([[1.0] + [0.0] * (dim - 1)], dtype=np.float32), (n - dim, 1))
        vectors = np.vstack([vectors, extra])
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    config = build_embedding_config(vectors, "2026-01-01T00:00:00+00:00", "sha256", n)
    index_path = tmp_path / "embedding.index"
    metadata_path = tmp_path / "embedding_metadata.json"
    config_path = tmp_path / "embedding_config.json"
    persist_index(index, _metadata(n), config, index_path, metadata_path, config_path)
    return index_path, metadata_path, config_path


def _retriever(tmp_path: Path, model: FakeModel | None = None) -> EmbeddingRetriever:
    index_path, metadata_path, config_path = _write_index(tmp_path)
    fake_model = model or FakeModel()
    return EmbeddingRetriever(
        index_path,
        metadata_path,
        config_path,
        catalog_path=None,
        model_provider=lambda: fake_model,
    )


def test_initialization_loads_index_and_model(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()

    health = retriever.health()
    assert health.index_loaded is True
    assert health.model_loaded is True
    assert health.metadata_loaded is True
    assert health.model_name == "BAAI/bge-small-en-v1.5"
    assert health.embedding_dimension == 3
    assert health.number_of_indexed_assessments == 3
    assert health.catalog_sha == "sha256"
    assert health.average_query_latency_ms is None


def test_singleton_model_provider_reused_across_searches(tmp_path: Path) -> None:
    model = FakeModel()
    provider_calls = 0
    index_path, metadata_path, config_path = _write_index(tmp_path)

    def provider() -> FakeModel:
        nonlocal provider_calls
        provider_calls += 1
        return model

    retriever = EmbeddingRetriever(
        index_path,
        metadata_path,
        config_path,
        catalog_path=None,
        model_provider=provider,
    )
    retriever.initialize()
    retriever.search("developer")
    retriever.search("developer")

    assert provider_calls == 1
    assert len(model.calls) == 2


def test_valid_query_returns_results(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("developer assessment", top_k=2)

    assert len(results) == 2
    assert results[0].entity_id == "id-0"
    assert results[0].retrieval_source == "embedding"
    assert results[0].embedding_rank == 1
    assert retriever.health().average_query_latency_ms is not None


def test_empty_query_raises(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()

    with pytest.raises(EmbeddingRetrieverError, match="empty"):
        retriever.search("   \n\t  ")


def test_unicode_query_is_nfkc_normalized(tmp_path: Path) -> None:
    model = FakeModel()
    retriever = _retriever(tmp_path, model)
    retriever.initialize()
    retriever.search("  ｕｎｉｃｏｄｅ   query  ")

    assert model.calls[0] == ["unicode query"]


def test_large_query_searches_successfully(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    query = "large " * 1000
    results = retriever.search(query, top_k=3)

    assert len(results) == 3


def test_threshold_filtering(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("developer", top_k=3, minimum_score=0.9)

    assert [result.entity_id for result in results] == ["id-0"]


def test_ranking_order(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("developer", top_k=3)

    assert [result.score for result in results] == sorted(
        [result.score for result in results],
        reverse=True,
    )


def test_metadata_resolution(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    result = retriever.search("developer", top_k=1)[0]

    assert result.name == "Assessment 0"
    assert result.url == "https://www.shl.com/0"
    assert result.job_levels == ["Graduate"]
    assert result.languages == ["English"]
    assert result.keys == ["Knowledge & Skills"]


def test_dimension_mismatch_from_query_embedding_raises(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path, FakeModel(dim=2))
    retriever.initialize()

    with pytest.raises(EmbeddingRetrieverError, match="Dimension mismatch"):
        retriever.search("developer")


def test_corrupted_faiss_raises(tmp_path: Path) -> None:
    index_path, metadata_path, config_path = _write_index(tmp_path)
    index_path.write_bytes(b"not faiss")
    retriever = EmbeddingRetriever(
        index_path,
        metadata_path,
        config_path,
        catalog_path=None,
        model_provider=lambda: FakeModel(),
    )

    with pytest.raises(EmbeddingRetrieverError):
        retriever.initialize()


def test_missing_metadata_raises(tmp_path: Path) -> None:
    index_path, metadata_path, config_path = _write_index(tmp_path)
    metadata_path.unlink()
    retriever = EmbeddingRetriever(
        index_path,
        metadata_path,
        config_path,
        catalog_path=None,
        model_provider=lambda: FakeModel(),
    )

    with pytest.raises(EmbeddingRetrieverError, match="Metadata"):
        retriever.initialize()


def test_configuration_mismatch_raises(tmp_path: Path) -> None:
    index_path, metadata_path, config_path = _write_index(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["embedding_dim"] = 2
    config_path.write_text(json.dumps(config), encoding="utf-8")
    retriever = EmbeddingRetriever(
        index_path,
        metadata_path,
        config_path,
        catalog_path=None,
        model_provider=lambda: FakeModel(),
    )

    with pytest.raises(EmbeddingRetrieverError, match="dimension"):
        retriever.initialize()


def test_deterministic_retrieval(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    first = retriever.search("developer", top_k=3)
    second = retriever.search("developer", top_k=3)

    assert [result.model_dump() for result in first] == [result.model_dump() for result in second]
