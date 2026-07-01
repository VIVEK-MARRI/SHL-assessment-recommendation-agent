"""Unit tests for retrieval.embedding_search."""

from __future__ import annotations

import faiss
import numpy as np
import pytest

from retrieval.embedding_search import EmbeddingSearchError, search_embeddings
from retrieval.models import AssessmentMetadataRecord


def _metadata(n: int) -> list[AssessmentMetadataRecord]:
    return [
        AssessmentMetadataRecord(
            offset=i,
            entity_id=f"id-{i}",
            name=f"Assessment {i}",
            url="https://www.shl.com/",
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


def _index() -> faiss.IndexFlatIP:
    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.8, 0.6, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    index = faiss.IndexFlatIP(3)
    index.add(vectors)
    return index


def test_search_embeddings_returns_ranked_metadata() -> None:
    results = search_embeddings(_index(), _metadata(3), np.array([1.0, 0.0, 0.0], dtype=np.float32))

    assert [result.entity_id for result in results] == ["id-0", "id-1", "id-2"]
    assert [result.rank for result in results] == [1, 2, 3]
    assert [result.embedding_rank for result in results] == [1, 2, 3]
    assert {result.retrieval_source for result in results} == {"embedding"}
    assert results[0].name == "Assessment 0"
    assert results[0].duration_minutes == 10


def test_top_k_limits_results() -> None:
    results = search_embeddings(
        _index(),
        _metadata(3),
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        top_k=2,
    )

    assert len(results) == 2


def test_threshold_filtering_removes_low_scores() -> None:
    results = search_embeddings(
        _index(),
        _metadata(3),
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        minimum_score=0.9,
    )

    assert [result.entity_id for result in results] == ["id-0"]


def test_ranking_order_is_descending() -> None:
    results = search_embeddings(_index(), _metadata(3), np.array([1.0, 0.0, 0.0], dtype=np.float32))
    scores = [result.score for result in results]

    assert scores == sorted(scores, reverse=True)


def test_metadata_count_mismatch_raises() -> None:
    with pytest.raises(EmbeddingSearchError, match="Metadata mismatch"):
        search_embeddings(_index(), _metadata(2), np.array([1.0, 0.0, 0.0], dtype=np.float32))


def test_dimension_mismatch_raises() -> None:
    with pytest.raises(EmbeddingSearchError, match="Dimension mismatch"):
        search_embeddings(_index(), _metadata(3), np.array([1.0, 0.0], dtype=np.float32))


def test_invalid_top_k_raises() -> None:
    with pytest.raises(EmbeddingSearchError, match="top_k"):
        search_embeddings(
            _index(),
            _metadata(3),
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            top_k=0,
        )


def test_deterministic_search_results() -> None:
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    first = search_embeddings(_index(), _metadata(3), query)
    second = search_embeddings(_index(), _metadata(3), query)

    assert [result.model_dump() for result in first] == [result.model_dump() for result in second]


def test_embedding_rank_preserves_raw_semantic_rank_after_deduplication() -> None:
    metadata = _metadata(3)
    metadata[1] = metadata[1].model_copy(update={"entity_id": "id-0", "name": "Duplicate"})

    results = search_embeddings(
        _index(),
        metadata,
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
    )

    assert [result.entity_id for result in results] == ["id-0", "id-2"]
    assert [result.rank for result in results] == [1, 2]
    assert [result.embedding_rank for result in results] == [1, 3]
