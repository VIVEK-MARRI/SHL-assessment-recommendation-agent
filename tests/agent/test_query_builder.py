"""Unit tests for the deterministic Query Builder (Module 14)."""

from __future__ import annotations

import pytest

from agent.conversation_models import ConversationState
from agent.query_builder import (
    InvalidConversationState,
    InvalidRoutingDecision,
    QueryBuilder,
)
from agent.routing_models import RouteType, RoutingDecision


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _recommend_decision() -> RoutingDecision:
    return RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="Sufficient info",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )


def _refine_decision() -> RoutingDecision:
    return RoutingDecision(
        route=RouteType.REFINE,
        next_module="query_builder",
        reason="Updated requirements",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )


def _compare_decision() -> RoutingDecision:
    return RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="Compare requested",
        confidence="HIGH",
        query_required=True,
        comparison_required=True,
    )


@pytest.fixture()
def builder() -> QueryBuilder:
    return QueryBuilder()


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------


def test_invalid_state_type(builder: QueryBuilder) -> None:
    with pytest.raises(InvalidConversationState):
        builder.build("not-a-state", _recommend_decision())  # type: ignore[arg-type]


def test_invalid_decision_type(builder: QueryBuilder) -> None:
    state = ConversationState(role="Engineer", technical_skills=["Python"])
    with pytest.raises(InvalidRoutingDecision):
        builder.build(state, "not-a-decision")  # type: ignore[arg-type]


def test_non_actionable_route_refuses(builder: QueryBuilder) -> None:
    state = ConversationState(role="Engineer", technical_skills=["Python"])
    decision = RoutingDecision(
        route=RouteType.REFUSE,
        next_module="refusal",
        reason="Off topic",
        confidence="LOW",
    )
    with pytest.raises(InvalidRoutingDecision):
        builder.build(state, decision)


def test_clarify_route_not_actionable(builder: QueryBuilder) -> None:
    state = ConversationState(role="Engineer")
    decision = RoutingDecision(
        route=RouteType.CLARIFY,
        next_module="clarification",
        reason="Missing skills",
        confidence="MEDIUM",
        clarification_field="technical_skills",
    )
    with pytest.raises(InvalidRoutingDecision):
        builder.build(state, decision)


# ---------------------------------------------------------------------------
# Backend Developer
# ---------------------------------------------------------------------------


def test_backend_developer(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Backend Developer",
        technical_skills=["Python", "SQL"],
    )
    query = builder.build(state, _recommend_decision())
    assert "Backend Developer" in query.query_text
    assert "backend" in query.expansion_terms
    assert "api" in query.expansion_terms
    assert "Knowledge & Skills" in query.filters.test_types
    assert query.filters.languages == ["English"]


# ---------------------------------------------------------------------------
# Python Developer
# ---------------------------------------------------------------------------


def test_python_developer_expansion(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Python Developer",
        technical_skills=["Django", "Flask"],
    )
    query = builder.build(state, _recommend_decision())
    assert "python" in query.expansion_terms
    assert "django" in query.expansion_terms
    assert "flask" in query.expansion_terms


# ---------------------------------------------------------------------------
# Sales Manager
# ---------------------------------------------------------------------------


def test_sales_manager_expansion(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Sales Manager",
        technical_skills=[],
        soft_skills=["communication", "negotiation"],
    )
    query = builder.build(state, _recommend_decision())
    assert "sales" in query.expansion_terms
    assert "leadership" in query.expansion_terms
    assert "communication" in query.optional_terms
    assert "negotiation" in query.optional_terms
    # No technical skills → Knowledge & Skills not in test_types
    assert "Knowledge & Skills" not in query.filters.test_types


# ---------------------------------------------------------------------------
# Leadership, personality, cognitive, simulation flags
# ---------------------------------------------------------------------------


def test_leadership_flag_adds_optional_term(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Team Lead",
        technical_skills=["Python"],
        leadership_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "leadership" in query.optional_terms


def test_personality_flag_adds_test_type(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="HR Manager",
        technical_skills=[],
        personality_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "Personality & Behavior" in query.filters.test_types
    assert "personality" in query.optional_terms


def test_cognitive_flag_adds_test_type(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Analyst",
        technical_skills=["SQL"],
        cognitive_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "Ability & Aptitude" in query.filters.test_types
    assert "cognitive" in query.optional_terms


def test_simulation_flag_adds_test_type(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Sales Representative",
        technical_skills=[],
        simulation_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "Simulations" in query.filters.test_types
    assert "simulation" in query.optional_terms


# ---------------------------------------------------------------------------
# Duration extraction
# ---------------------------------------------------------------------------


def test_duration_minutes(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python"],
        constraints=["maximum 30 minutes"],
    )
    query = builder.build(state, _recommend_decision())
    assert query.filters.maximum_duration_minutes == 30


def test_duration_hours(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python"],
        constraints=["must complete within 1 hour"],
    )
    query = builder.build(state, _recommend_decision())
    assert query.filters.maximum_duration_minutes == 60


def test_duration_minutes_shorthand(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python"],
        constraints=["under 45 min"],
    )
    query = builder.build(state, _recommend_decision())
    assert query.filters.maximum_duration_minutes == 45


def test_no_duration_constraint(builder: QueryBuilder) -> None:
    state = ConversationState(role="Engineer", technical_skills=["Java"])
    query = builder.build(state, _recommend_decision())
    assert query.filters.maximum_duration_minutes is None


# ---------------------------------------------------------------------------
# Job level mapping
# ---------------------------------------------------------------------------


def test_seniority_junior_maps_to_entry_level(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Developer",
        technical_skills=["Java"],
        seniority="Junior",
    )
    query = builder.build(state, _recommend_decision())
    assert "Entry Level" in query.filters.job_levels


def test_seniority_senior_maps_to_manager(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Developer",
        technical_skills=["Java"],
        seniority="Senior",
    )
    query = builder.build(state, _recommend_decision())
    assert "Manager" in query.filters.job_levels


def test_seniority_intern(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Developer",
        technical_skills=["Python"],
        seniority="Intern",
    )
    query = builder.build(state, _recommend_decision())
    assert "Entry Level" in query.filters.job_levels


def test_seniority_director(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Product Manager",
        technical_skills=[],
        seniority="Director",
    )
    query = builder.build(state, _compare_decision())
    assert "Director" in query.filters.job_levels


def test_no_seniority_empty_job_levels(builder: QueryBuilder) -> None:
    state = ConversationState(role="Developer", technical_skills=["Go"])
    query = builder.build(state, _recommend_decision())
    assert query.filters.job_levels == []


# ---------------------------------------------------------------------------
# Language filter
# ---------------------------------------------------------------------------


def test_language_defaults_to_english(builder: QueryBuilder) -> None:
    state = ConversationState(role="Engineer", technical_skills=["Python"])
    query = builder.build(state, _recommend_decision())
    assert query.filters.languages == ["English"]


# ---------------------------------------------------------------------------
# Negative constraints (excluded terms)
# ---------------------------------------------------------------------------


def test_no_personality_excluded(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Analyst",
        technical_skills=["SQL"],
        constraints=["no personality tests"],
        personality_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "Personality" in query.excluded_terms
    # Also must NOT appear in test_types
    assert "Personality & Behavior" not in query.filters.test_types


def test_no_simulation_excluded(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Developer",
        technical_skills=["Python"],
        constraints=["no simulation required"],
        simulation_required=True,
    )
    query = builder.build(state, _recommend_decision())
    assert "Simulation" in query.excluded_terms
    assert "Simulations" not in query.filters.test_types


def test_exclude_opq_explicit(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="HR Manager",
        technical_skills=[],
        constraints=["do not recommend OPQ"],
    )
    query = builder.build(state, _recommend_decision())
    assert "OPQ" in query.excluded_terms


# ---------------------------------------------------------------------------
# Refine support
# ---------------------------------------------------------------------------


def test_refine_builds_fresh_from_current_state(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Backend Developer",
        technical_skills=["Python", "Java"],
        constraints=["maximum 45 minutes"],
    )
    query = builder.build(state, _refine_decision())
    assert "Backend Developer" in query.query_text
    assert "Python" in query.required_terms
    assert "Java" in query.required_terms
    assert query.filters.maximum_duration_minutes == 45


# ---------------------------------------------------------------------------
# Duplicate removal
# ---------------------------------------------------------------------------


def test_no_duplicate_tokens(builder: QueryBuilder) -> None:
    # "backend" appears in expansion AND soft skills — must not duplicate
    state = ConversationState(
        role="Backend Developer",
        technical_skills=["Python"],
        soft_skills=["backend"],  # deliberate duplicate of expansion term
    )
    query = builder.build(state, _recommend_decision())
    lower_tokens = [t.lower() for t in query.query_tokens]
    assert len(lower_tokens) == len(set(lower_tokens))


# ---------------------------------------------------------------------------
# Deterministic ordering
# ---------------------------------------------------------------------------


def test_deterministic_ordering(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Python Developer",
        technical_skills=["Django", "Flask"],
    )
    first = builder.build(state, _recommend_decision())
    second = builder.build(state, _recommend_decision())
    assert first.query_tokens == second.query_tokens
    assert first.query_text == second.query_text


# ---------------------------------------------------------------------------
# Skill normalisation in query
# ---------------------------------------------------------------------------


def test_cpp_normalisation(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Embedded Engineer",
        technical_skills=["C++"],
    )
    query = builder.build(state, _recommend_decision())
    tokens_lower = [t.lower() for t in query.query_tokens]
    assert "cpp" in tokens_lower


def test_machine_learning_normalisation(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Data Scientist",
        technical_skills=["Machine Learning"],
    )
    query = builder.build(state, _recommend_decision())
    tokens_lower = [t.lower() for t in query.query_tokens]
    assert "ml" in tokens_lower


# ---------------------------------------------------------------------------
# Compare route
# ---------------------------------------------------------------------------


def test_compare_route_builds_query(builder: QueryBuilder) -> None:
    state = ConversationState(
        role="Sales Manager",
        technical_skills=[],
        mentioned_assessment_names=["OPQ32", "MQ"],
        comparison_requested=True,
    )
    query = builder.build(state, _compare_decision())
    assert "Sales Manager" in query.query_text
    assert query.filters.languages == ["English"]
