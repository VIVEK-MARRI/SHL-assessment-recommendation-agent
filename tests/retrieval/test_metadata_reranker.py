"""Unit tests for the deterministic MetadataReranker."""

from __future__ import annotations

from agent.conversation_models import ConversationState
from agent.query_models import QueryFilters
from retrieval.metadata_reranker import MetadataReranker
from retrieval.retrieval_models import RetrievedAssessment


def test_reranker_skill_boost() -> None:
    """Test exact skill boosting logic."""
    results = [
        RetrievedAssessment(
            entity_id="1",
            name="General Assessment",
            description="A very generic test",
            url="https://shl.com/1",
            score=10.0,
            rank=1,
            keys=[],
        ),
        RetrievedAssessment(
            entity_id="2",
            name="Python Developer",
            description="A test for Python developers",
            url="https://shl.com/2",
            score=5.0,
            rank=2,
            keys=["python_dev"],
        ),
        RetrievedAssessment(
            entity_id="3",
            name="Java Backend",
            description="Testing java skills and some python.",
            url="https://shl.com/3",
            score=7.0,
            rank=3,
            keys=["java"],
        ),
    ]

    state = ConversationState(technical_skills=["Python"])
    filters = QueryFilters()
    
    reranked = MetadataReranker.rerank(results, state, filters)
    
    # Python Developer (score=5 + 100 name match = 105) should be rank 1
    assert reranked[0].entity_id == "2"
    # Java Backend (score=7 + 20 desc match - 50 tech penalty = -23) should be last
    # General Assessment (score=10) should be rank 2
    assert reranked[1].entity_id == "1"
    assert reranked[2].entity_id == "3"


def test_reranker_technology_penalty() -> None:
    """Test penalty for unrelated technologies."""
    results = [
        RetrievedAssessment(
            entity_id="1",
            name="Java Backend Developer",
            description="A test for java",
            url="https://shl.com/1",
            score=20.0,
            rank=1,
        ),
        RetrievedAssessment(
            entity_id="2",
            name="C# Assessment",
            description="A test for C#",
            url="https://shl.com/2",
            score=15.0,
            rank=2,
        ),
        RetrievedAssessment(
            entity_id="3",
            name="Python Engineer",
            description="Python test",
            url="https://shl.com/3",
            score=10.0,
            rank=3,
        ),
    ]

    # Query requests Python
    state = ConversationState(technical_skills=["Python"])
    filters = QueryFilters()
    
    reranked = MetadataReranker.rerank(results, state, filters)
    
    # 3 should be boosted (+100) -> 110
    # 1 should be penalized (-50) -> -30
    # 2 should be penalized (-50) -> -35
    assert reranked[0].entity_id == "3"
    assert reranked[1].entity_id == "1"
    assert reranked[2].entity_id == "2"


def test_reranker_constraint_penalty() -> None:
    """Test filtering by explicit constraints."""
    results = [
        RetrievedAssessment(
            entity_id="1",
            name="Test A",
            description="",
            url="https://shl.com/1",
            score=20.0,
            rank=1,
            duration_minutes=60,
            languages=["English"],
        ),
        RetrievedAssessment(
            entity_id="2",
            name="Test B",
            description="",
            url="https://shl.com/2",
            score=10.0,
            rank=2,
            duration_minutes=20,
            languages=["French"],
        ),
    ]

    state = ConversationState()
    # Filter: duration <= 30
    filters = QueryFilters(maximum_duration_minutes=30)
    
    reranked = MetadataReranker.rerank(results, state, filters)
    # Test A (duration=60) penalized by -10000 -> -9980
    # Test B (duration=20) unchanged -> 10.0
    assert reranked[0].entity_id == "2"
    assert reranked[1].entity_id == "1"


def test_python_exact_match_beats_unrelated_r_assessment() -> None:
    results = [
        RetrievedAssessment(
            entity_id="r",
            name="R Programming (New)",
            description="Measures R programming skills.",
            url="https://shl.com/r",
            score=0.04,
            rrf_score=0.04,
            rank=1,
            embedding_rank=1,
            bm25_rank=1,
            keys=["Knowledge & Skills"],
        ),
        RetrievedAssessment(
            entity_id="py",
            name="Python (New)",
            description="Measures Python programming skills.",
            url="https://shl.com/python",
            score=0.03,
            rrf_score=0.03,
            rank=2,
            embedding_rank=2,
            bm25_rank=2,
            keys=["Knowledge & Skills"],
        ),
    ]

    state = ConversationState(role="Senior Engineer", seniority="senior", technical_skills=["Python"])
    reranked = MetadataReranker.rerank(results, state, QueryFilters(test_types=["Knowledge & Skills"]))

    assert [item.entity_id for item in reranked] == ["py", "r"]


def test_reranker_penalizes_explicit_negative_capability() -> None:
    results = [
        RetrievedAssessment(
            entity_id="opq",
            name="OPQ Leadership Report",
            description="Personality and leadership behavior report.",
            url="https://shl.com/opq",
            score=20.0,
            rank=1,
            keys=["Personality & Behavior"],
        ),
        RetrievedAssessment(
            entity_id="java",
            name="Java Programming",
            description="Knowledge and skills assessment.",
            url="https://shl.com/java",
            score=10.0,
            rank=2,
            keys=["Knowledge & Skills"],
        ),
    ]

    state = ConversationState(technical_skills=["Java"], constraints=["No personality."])
    reranked = MetadataReranker.rerank(results, state, QueryFilters(test_types=["Knowledge & Skills"]))

    assert [item.entity_id for item in reranked] == ["java", "opq"]


def test_reranker_technology_penalty_from_catalog_dynamic_vocabulary() -> None:
    results = [
        RetrievedAssessment(
            entity_id="1",
            name="OPQ32r",
            description="Occupational Personality Questionnaire",
            url="https://shl.com/opq",
            score=10.0,
            rank=1,
        ),
        RetrievedAssessment(
            entity_id="2",
            name="Python Developer",
            description="Python test",
            url="https://shl.com/2",
            score=5.0,
            rank=2,
        ),
    ]
    state = ConversationState(technical_skills=["Python"])
    reranked = MetadataReranker.rerank(results, state, QueryFilters())
    assert reranked[0].entity_id == "2"


def test_reranker_tie_break_is_deterministic() -> None:
    results = [
        RetrievedAssessment(entity_id="b", name="Assessment B", url="https://shl.com/b", score=1.0, rank=1),
        RetrievedAssessment(entity_id="a", name="Assessment A", url="https://shl.com/a", score=1.0, rank=2),
    ]

    first = MetadataReranker.rerank(results, ConversationState(), QueryFilters())
    second = MetadataReranker.rerank(results, ConversationState(), QueryFilters())

    assert [item.entity_id for item in first] == ["a", "b"]
    assert [item.entity_id for item in second] == ["a", "b"]
