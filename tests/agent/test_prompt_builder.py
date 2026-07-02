import pytest

from agent.conversation_models import ConversationMessage, ConversationState
from agent.comparison_models import ComparisonAssessment, ComparisonContext
from agent.prompt_builder import (
    PromptBuilder,
    PromptBuilderError,
    InvalidPromptRoute,
    MissingGroundingContext,
)
from agent.prompt_models import GroundingAssessment, PromptPackage
from agent.prompt_templates import PromptTemplates, TemplateLoadError
from agent.routing_models import RouteType, RoutingDecision
from retrieval.retrieval_models import RetrievedAssessment


@pytest.fixture
def templates() -> PromptTemplates:
    return PromptTemplates()


@pytest.fixture
def builder(templates: PromptTemplates) -> PromptBuilder:
    return PromptBuilder(templates=templates)


@pytest.fixture
def conversation() -> list[ConversationMessage]:
    return [
        ConversationMessage(role="user", content="I need a Python test."),
        ConversationMessage(role="assistant", content="What seniority level?"),
        ConversationMessage(role="user", content="Senior level."),
    ]


@pytest.fixture
def state() -> ConversationState:
    return ConversationState(role="Python Developer", seniority="Senior")


@pytest.fixture
def retrieved_assessments() -> list[RetrievedAssessment]:
    return [
        RetrievedAssessment(
            entity_id="1",
            name="Python Assessment 1",
            url="http://test1",
            score=0.9,
            rank=1,
            test_type="Knowledge",
            duration="30 min",
            job_levels=["Senior"],
            languages=["English"],
            remote=True,
            adaptive=False,
            keys=["Knowledge"],
        ),
        RetrievedAssessment(
            entity_id="2",
            name="Python Assessment 2",
            url="http://test2",
            score=0.8,
            rank=2,
            test_type="Simulation",
            duration="45 min",
            job_levels=["Senior"],
            languages=["English"],
            remote=True,
            adaptive=True,
            keys=["Simulation"],
        ),
        # Duplicate to test dedup
        RetrievedAssessment(
            entity_id="1",
            name="Python Assessment 1",
            url="http://test1",
            score=0.7,
            rank=3,
            test_type="Knowledge",
            duration="30 min",
            job_levels=["Senior"],
            languages=["English"],
            remote=True,
            adaptive=False,
            keys=["Knowledge"],
        ),
    ]


@pytest.fixture
def comparison_context() -> ComparisonContext:
    return ComparisonContext(
        comparison_possible=True,
        reason="Found 2",
        matched_assessments=[
            ComparisonAssessment(
                entity_id="3",
                name="Java Assessment 1",
                url="http://java1",
                test_type=["Knowledge"],
                description="Desc 1",
                job_levels=["Mid"],
                languages=["English"],
                duration="20 min",
            ),
            ComparisonAssessment(
                entity_id="4",
                name="Java Assessment 2",
                url="http://java2",
                test_type=["Simulation"],
                description="Desc 2",
                job_levels=["Mid"],
                languages=["English"],
                duration="40 min",
            ),
        ],
    )


def test_template_loading(templates: PromptTemplates) -> None:
    rec = templates.get_template(RouteType.RECOMMEND)
    assert "SHL assessment consultant" in rec
    assert "Never recommend assessments outside the supplied list" in rec
    assert "GROUNDING CONTEXT" in rec

    comp = templates.get_template(RouteType.COMPARE)
    assert "compare" in comp
    assert "Purpose" in comp or "SHL Individual Test Solutions catalog" in comp

    clar = templates.get_template(RouteType.CLARIFY)
    assert "exactly ONE clarification question" in clar

    ref = templates.get_template(RouteType.REFUSE)
    assert "Politely decline" in ref or "Politely refuse" in ref


def test_template_caching(templates: PromptTemplates) -> None:
    rec1 = templates.get_template(RouteType.RECOMMEND)
    rec2 = templates.get_template(RouteType.RECOMMEND)
    assert rec1 is rec2


def test_missing_template(tmp_path) -> None:
    # Use empty dir
    templates = PromptTemplates(templates_dir=tmp_path)
    with pytest.raises(TemplateLoadError):
        templates.get_template(RouteType.RECOMMEND)


def test_recommendation_route(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
    retrieved_assessments: list[RetrievedAssessment],
) -> None:
    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="ok",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
        retrieved_assessments=retrieved_assessments,
    )

    assert isinstance(package, PromptPackage)
    assert package.route == RouteType.RECOMMEND
    assert "Never recommend" in package.system_prompt
    assert "User:\nI need a Python test." in package.user_prompt
    assert "Assistant:\nWhat seniority level?" in package.user_prompt
    assert len(package.grounding_assessments) == 2  # Deduped
    assert package.grounding_assessments[0].name == "Python Assessment 1"
    assert package.grounding_assessments[1].name == "Python Assessment 2"
    assert package.metadata.assessment_count == 2
    assert package.metadata.conversation_turns == 3


def test_refine_route_uses_recommendation(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
    retrieved_assessments: list[RetrievedAssessment],
) -> None:
    decision = RoutingDecision(
        route=RouteType.REFINE,
        next_module="query_builder",
        reason="ok",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
        retrieved_assessments=retrieved_assessments,
    )

    assert package.route == RouteType.REFINE
    assert "Never recommend" in package.system_prompt  # Uses recommend template
    assert len(package.grounding_assessments) == 2


def test_recommendation_missing_context(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
) -> None:
    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="ok",
        confidence="HIGH",
    )
    with pytest.raises(MissingGroundingContext):
        builder.build(conversation=conversation, state=state, decision=decision)


def test_comparison_route(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
    comparison_context: ComparisonContext,
) -> None:
    decision = RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="ok",
        confidence="HIGH",
        comparison_required=True,
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
        comparison_context=comparison_context,
    )

    assert package.route == RouteType.COMPARE
    assert "Purpose" in package.system_prompt or "compare" in package.system_prompt
    assert "SHL assessment consultant" in package.system_prompt
    assert len(package.grounding_assessments) == 2
    assert package.grounding_assessments[0].name == "Java Assessment 1"


def test_comparison_missing_context(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
) -> None:
    decision = RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="ok",
        confidence="HIGH",
    )
    with pytest.raises(MissingGroundingContext):
        builder.build(conversation=conversation, state=state, decision=decision)


def test_clarification_route(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
) -> None:
    decision = RoutingDecision(
        route=RouteType.CLARIFY,
        next_module="clarification",
        reason="ok",
        confidence="HIGH",
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
    )

    assert package.route == RouteType.CLARIFY
    assert "exactly ONE clarification question" in package.system_prompt
    assert len(package.grounding_assessments) == 0


def test_refusal_route(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
) -> None:
    decision = RoutingDecision(
        route=RouteType.REFUSE,
        next_module="refusal",
        reason="ok",
        confidence="HIGH",
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
    )

    assert package.route == RouteType.REFUSE
    assert "Politely decline" in package.system_prompt or "Politely refuse" in package.system_prompt
    assert len(package.grounding_assessments) == 0


def test_assessment_limit(
    builder: PromptBuilder,
    conversation: list[ConversationMessage],
    state: ConversationState,
) -> None:
    # Create 10 distinct retrieved assessments
    retrieved = [
        RetrievedAssessment(
            entity_id=str(i),
            name=f"Assessment {i}",
            url=f"http://test{i}",
            score=0.9,
            rank=i,
        )
        for i in range(1, 11)
    ]

    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="ok",
        confidence="HIGH",
    )

    package = builder.build(
        conversation=conversation,
        state=state,
        decision=decision,
        retrieved_assessments=retrieved,
    )

    assert len(package.grounding_assessments) == 8  # Capped at 8
    assert package.metadata.assessment_count == 8
    # Ordering preserved
    assert package.grounding_assessments[0].name == "Assessment 1"
    assert package.grounding_assessments[7].name == "Assessment 8"
