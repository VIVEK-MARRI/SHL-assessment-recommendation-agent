"""Unit tests for retrieval.confidence_gate."""

from __future__ import annotations

import pytest

from retrieval.confidence_gate import ConfidenceGate, ConfidenceGateError
from retrieval.retrieval_models import RetrievedAssessment


def _hybrid(entity_id: str, rrf_score: float = 0.03) -> RetrievedAssessment:
    return RetrievedAssessment(
        retrieval_source="hybrid",
        entity_id=entity_id,
        name=f"Assessment {entity_id}",
        url=f"https://www.shl.com/{entity_id}",
        score=rrf_score,
        rrf_score=rrf_score,
        rank=1,
    )


def _source(entity_id: str, source: str) -> RetrievedAssessment:
    return RetrievedAssessment(
        retrieval_source=source,
        entity_id=entity_id,
        name=f"Assessment {entity_id}",
        url=f"https://www.shl.com/{entity_id}",
        score=1.0,
        rank=1,
        embedding_rank=1 if source == "embedding" else None,
        bm25_rank=1 if source == "bm25" else None,
    )


def test_confidence_high() -> None:
    result = ConfidenceGate().evaluate(
        [_hybrid("a")],
        [_source("a", "embedding")],
        [_source("a", "bm25")],
    )

    assert result.confidence == "HIGH"
    assert result.reason == "Strong agreement"


def test_confidence_medium_for_partial_overlap_with_weak_lexical_support() -> None:
    result = ConfidenceGate(minimum_overlap=2).evaluate(
        [_hybrid("a")],
        [_source("a", "embedding"), _source("b", "embedding")],
        [_source("a", "bm25")],
    )

    assert result.confidence == "MEDIUM"
    assert result.reason == "Weak lexical support"


def test_confidence_medium_for_partial_overlap_with_weak_semantic_support() -> None:
    result = ConfidenceGate(minimum_overlap=2).evaluate(
        [_hybrid("a")],
        [_source("a", "embedding")],
        [_source("a", "bm25"), _source("b", "bm25")],
    )

    assert result.confidence == "MEDIUM"
    assert result.reason == "Weak semantic support"


def test_confidence_low_for_no_overlap() -> None:
    result = ConfidenceGate().evaluate(
        [_hybrid("a")],
        [_source("a", "embedding")],
        [_source("b", "bm25")],
    )

    assert result.confidence == "LOW"
    assert result.reason == "Insufficient evidence"


def test_confidence_low_for_weak_top_score() -> None:
    result = ConfidenceGate(minimum_rrf_score=0.05).evaluate(
        [_hybrid("a", rrf_score=0.01)],
        [_source("a", "embedding")],
        [_source("a", "bm25")],
    )

    assert result.confidence == "LOW"


def test_empty_results_raise() -> None:
    with pytest.raises(ConfidenceGateError, match="empty"):
        ConfidenceGate().evaluate([], [], [])


def test_missing_rrf_score_raises() -> None:
    result = _hybrid("a").model_copy(update={"rrf_score": None})

    with pytest.raises(ConfidenceGateError, match="rrf_score"):
        ConfidenceGate().evaluate(
            [result],
            [_source("a", "embedding")],
            [_source("a", "bm25")],
        )

