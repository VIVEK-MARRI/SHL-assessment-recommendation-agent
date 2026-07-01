"""Unit tests for retrieval.bm25_search."""

from __future__ import annotations

from rank_bm25 import BM25Okapi
import pytest

from retrieval.bm25_models import BM25DocumentRecord
from retrieval.bm25_search import BM25SearchError, search_bm25


def _documents() -> list[BM25DocumentRecord]:
    return [
        BM25DocumentRecord(
            offset=0,
            entity_id="java",
            document="Name:\nJava Developer\n\nCategories:\nKnowledge & Skills (K)",
            tokens=["java", "developer", "coding"],
            name="Java Developer",
            url="https://www.shl.com/java",
            test_type="K",
            keys=["Knowledge & Skills"],
            job_levels=["Graduate"],
            languages=["English"],
            duration="20 minutes",
            duration_minutes=20,
        ),
        BM25DocumentRecord(
            offset=1,
            entity_id="python",
            document="Name:\nPython Developer\n\nCategories:\nKnowledge & Skills (K)",
            tokens=["python", "developer", "coding"],
            name="Python Developer",
            url="https://www.shl.com/python",
            test_type="K",
            keys=["Knowledge & Skills"],
            job_levels=["Professional"],
            languages=["English"],
            duration="30 minutes",
            duration_minutes=30,
        ),
        BM25DocumentRecord(
            offset=2,
            entity_id="sales",
            document="Name:\nSales Manager\n\nCategories:\nPersonality & Behavior (P)",
            tokens=["sales", "manager", "personality"],
            name="Sales Manager",
            url="https://www.shl.com/sales",
            test_type="P",
            keys=["Personality & Behavior"],
        ),
    ]


def _index() -> BM25Okapi:
    return BM25Okapi([record.tokens for record in _documents()])


def test_search_bm25_returns_ranked_metadata() -> None:
    results = search_bm25(_index(), _documents(), ["python"], top_k=2)

    assert results[0].entity_id == "python"
    assert results[0].retrieval_source == "bm25"
    assert results[0].bm25_rank == 1
    assert results[0].embedding_rank is None
    assert results[0].name == "Python Developer"
    assert results[0].url == "https://www.shl.com/python"


def test_top_k_limits_results() -> None:
    results = search_bm25(_index(), _documents(), ["developer"], top_k=1)

    assert len(results) == 1


def test_threshold_filtering_removes_low_scores() -> None:
    results = search_bm25(_index(), _documents(), ["python"], minimum_score=0.1)

    assert [result.entity_id for result in results] == ["python"]


def test_ranking_order_is_descending() -> None:
    results = search_bm25(_index(), _documents(), ["developer"], top_k=3)
    scores = [result.score for result in results]

    assert scores == sorted(scores, reverse=True)


def test_metadata_count_mismatch_raises() -> None:
    with pytest.raises(BM25SearchError, match="Corpus mismatch"):
        search_bm25(_index(), _documents()[:2], ["python"])


def test_invalid_top_k_raises() -> None:
    with pytest.raises(BM25SearchError, match="top_k"):
        search_bm25(_index(), _documents(), ["python"], top_k=0)


def test_empty_query_tokens_raise() -> None:
    with pytest.raises(BM25SearchError, match="query_tokens"):
        search_bm25(_index(), _documents(), [])


def test_deterministic_search_results() -> None:
    first = search_bm25(_index(), _documents(), ["developer"], top_k=3)
    second = search_bm25(_index(), _documents(), ["developer"], top_k=3)

    assert [result.model_dump() for result in first] == [result.model_dump() for result in second]


def test_legacy_document_metadata_is_resolved() -> None:
    documents = [
        BM25DocumentRecord(
            offset=0,
            entity_id="legacy",
            document=(
                "Name:\nLegacy Assessment\n\n"
                "Categories:\nKnowledge & Skills (K)\n\n"
                "Job Levels:\nGraduate, Entry Level\n\n"
                "Languages:\nEnglish, Spanish\n\n"
                "Duration:\n15 minutes\n\n"
                "Remote:\nYes\n\n"
                "Adaptive:\nNo"
            ),
            tokens=["legacy", "assessment"],
        )
    ]
    index = BM25Okapi([documents[0].tokens])

    result = search_bm25(index, documents, ["legacy"], top_k=1, minimum_score=-1.0)[0]

    assert result.name == "Legacy Assessment"
    assert result.test_type == "K"
    assert result.keys == ["Knowledge & Skills"]
    assert result.job_levels == ["Graduate", "Entry Level"]
    assert result.duration_minutes == 15
