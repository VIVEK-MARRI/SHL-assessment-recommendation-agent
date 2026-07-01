"""Unit tests for retrieval.reciprocal_rank_fusion."""

from __future__ import annotations

import pytest

from retrieval.reciprocal_rank_fusion import RRFError, reciprocal_rank_fusion
from retrieval.retrieval_models import RetrievedAssessment


def _result(
    entity_id: str,
    source: str,
    rank: int,
    score: float = 1.0,
) -> RetrievedAssessment:
    return RetrievedAssessment(
        retrieval_source=source,
        entity_id=entity_id,
        name=f"Assessment {entity_id}",
        url=f"https://www.shl.com/{entity_id}",
        test_type="K",
        score=score,
        rank=rank,
        embedding_rank=rank if source == "embedding" else None,
        bm25_rank=rank if source == "bm25" else None,
        keys=["Knowledge & Skills"],
    )


def test_rrf_score_calculation() -> None:
    results = reciprocal_rank_fusion(
        [_result("a", "embedding", 1)],
        [_result("a", "bm25", 2)],
    )

    expected = (1 / 61) + (1 / 62)
    assert results[0].entity_id == "a"
    assert results[0].rrf_score == pytest.approx(expected)
    assert results[0].score == pytest.approx(expected)


def test_duplicate_merging_by_entity_id() -> None:
    results = reciprocal_rank_fusion(
        [_result("same", "embedding", 1)],
        [_result("same", "bm25", 1)],
    )

    assert len(results) == 1
    assert results[0].retrieval_source == "hybrid"
    assert results[0].embedding_rank == 1
    assert results[0].bm25_rank == 1


def test_entity_merge_does_not_merge_by_name_or_url() -> None:
    embedding = _result("a", "embedding", 1)
    bm25 = _result("b", "bm25", 1)
    bm25 = bm25.model_copy(update={"name": embedding.name, "url": embedding.url})

    results = reciprocal_rank_fusion([embedding], [bm25])

    assert {result.entity_id for result in results} == {"a", "b"}


def test_rank_preservation() -> None:
    results = reciprocal_rank_fusion(
        [_result("a", "embedding", 3)],
        [_result("a", "bm25", 4)],
    )

    assert results[0].embedding_rank == 3
    assert results[0].bm25_rank == 4


def test_deterministic_output() -> None:
    embedding = [_result("b", "embedding", 1), _result("a", "embedding", 1)]
    first = reciprocal_rank_fusion(embedding, [])
    second = reciprocal_rank_fusion(embedding, [])

    assert [result.model_dump() for result in first] == [
        result.model_dump() for result in second
    ]


def test_empty_retrieval_raises() -> None:
    with pytest.raises(RRFError, match="empty"):
        reciprocal_rank_fusion([], [])


def test_missing_rank_raises() -> None:
    bad = _result("a", "embedding", 1).model_copy(update={"embedding_rank": None})

    with pytest.raises(RRFError, match="embedding_rank"):
        reciprocal_rank_fusion([bad], [])

