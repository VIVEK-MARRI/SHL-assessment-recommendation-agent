"""Unit tests for the Comparison Pipeline (Module 15)."""

from __future__ import annotations

import pytest

from agent.catalog_matcher import CatalogMatcher
from agent.comparison import ComparisonError, ComparisonPipeline, InvalidComparisonRequest
from agent.comparison_models import ComparisonContext
from agent.conversation_models import ConversationState
from agent.routing_models import RouteType, RoutingDecision


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline() -> ComparisonPipeline:
    matcher = CatalogMatcher()
    matcher.load()
    return ComparisonPipeline(matcher=matcher)


def _compare_decision() -> RoutingDecision:
    return RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="User requested comparison",
        confidence="HIGH",
        query_required=True,
        comparison_required=True,
    )


def _recommend_decision() -> RoutingDecision:
    return RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="Sufficient info",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

def test_invalid_state_type(pipeline: ComparisonPipeline) -> None:
    with pytest.raises(InvalidComparisonRequest):
        pipeline.run("not-a-state", _compare_decision())  # type: ignore[arg-type]


def test_invalid_decision_type(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(mentioned_assessment_names=["Python (New)"])
    with pytest.raises(InvalidComparisonRequest):
        pipeline.run(state, "not-a-decision")  # type: ignore[arg-type]


def test_non_compare_route_raises(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(mentioned_assessment_names=["Python (New)"])
    with pytest.raises(InvalidComparisonRequest):
        pipeline.run(state, _recommend_decision())


# ---------------------------------------------------------------------------
# Two assessments — comparison possible
# ---------------------------------------------------------------------------

def test_two_known_assessments(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=["Python (New)", "Agile Software Development"]
    )
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is True
    assert len(ctx.matched_assessments) == 2
    assert ctx.unmatched_names == []


def test_three_assessments(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=[
            "Python (New)",
            "Agile Software Development",
            "Java 8 (New)",
        ]
    )
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is True
    assert len(ctx.matched_assessments) == 3


# ---------------------------------------------------------------------------
# One assessment — comparison not possible
# ---------------------------------------------------------------------------

def test_one_assessment_not_possible(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(mentioned_assessment_names=["Python (New)"])
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is False
    assert "at least two" in ctx.reason.lower()
    assert len(ctx.matched_assessments) == 1


# ---------------------------------------------------------------------------
# Unknown assessments — never invent
# ---------------------------------------------------------------------------

def test_unknown_assessment_is_unmatched(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=["Rust Assessment Does Not Exist"]
    )
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is False
    assert "Rust Assessment Does Not Exist" in ctx.unmatched_names
    assert ctx.matched_assessments == []


def test_mixed_known_and_unknown(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=[
            "Python (New)",
            "Totally Made Up Assessment",
        ]
    )
    ctx = pipeline.run(state, _compare_decision())
    # One matched — not enough for comparison
    assert ctx.comparison_possible is False
    assert len(ctx.matched_assessments) == 1
    assert "Totally Made Up Assessment" in ctx.unmatched_names


def test_two_known_one_unknown(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=[
            "Python (New)",
            "Agile Software Development",
            "Fake Assessment 999",
        ]
    )
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is True
    assert len(ctx.matched_assessments) == 2
    assert "Fake Assessment 999" in ctx.unmatched_names


# ---------------------------------------------------------------------------
# No assessments mentioned
# ---------------------------------------------------------------------------

def test_empty_assessment_names(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(mentioned_assessment_names=[])
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is False
    assert ctx.matched_assessments == []
    assert ctx.unmatched_names == []


# ---------------------------------------------------------------------------
# Ordering preserved
# ---------------------------------------------------------------------------

def test_ordering_preserved(pipeline: ComparisonPipeline) -> None:
    names = ["Agile Software Development", "Python (New)", "Java 8 (New)"]
    state = ConversationState(mentioned_assessment_names=names)
    ctx = pipeline.run(state, _compare_decision())
    returned_names = [a.name for a in ctx.matched_assessments]
    assert returned_names == [
        "Agile Software Development",
        "Python (New)",
        "Java 8 (New)",
    ]


# ---------------------------------------------------------------------------
# Case-insensitive resolution via pipeline
# ---------------------------------------------------------------------------

def test_pipeline_case_insensitive(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=["python (new)", "agile software development"]
    )
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is True
    assert len(ctx.matched_assessments) == 2


# ---------------------------------------------------------------------------
# Duplicate names in input
# ---------------------------------------------------------------------------

def test_duplicate_names(pipeline: ComparisonPipeline) -> None:
    # ConversationState deduplicates list entries via normalize_string_list,
    # so only one unique name is stored — not enough for comparison.
    state = ConversationState(
        mentioned_assessment_names=["Python (New)", "Python (New)"]
    )
    assert len(state.mentioned_assessment_names) == 1
    ctx = pipeline.run(state, _compare_decision())
    assert ctx.comparison_possible is False
    assert "at least two" in ctx.reason.lower()


# ---------------------------------------------------------------------------
# ComparisonContext fields populated correctly
# ---------------------------------------------------------------------------

def test_context_fields_populated(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(
        mentioned_assessment_names=["Python (New)", "Agile Software Development"]
    )
    ctx = pipeline.run(state, _compare_decision())
    for assessment in ctx.matched_assessments:
        assert assessment.entity_id != ""
        assert assessment.url.startswith("http")
        assert assessment.name != ""
        assert isinstance(assessment.keys, list)
        assert isinstance(assessment.job_levels, list)
        assert isinstance(assessment.languages, list)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_comparison_context(pipeline: ComparisonPipeline) -> None:
    state = ConversationState(mentioned_assessment_names=["Python (New)"])
    ctx = pipeline.run(state, _compare_decision())
    assert isinstance(ctx, ComparisonContext)
