"""Service-level orchestration regressions."""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.comparison_models import ComparisonContext
from agent.conversation_models import ConversationMessage, ConversationState
from agent.generation_models import LLMGenerationResult
from agent.response_models import ChatResponse
from agent.routing_models import RouteType, RoutingDecision
from agent.validator_models import ValidatedGenerationResult
from app.services.chat_service import ChatService


def test_comparison_route_passes_decision_to_pipeline() -> None:
    state = ConversationState(
        comparison_requested=True,
        mentioned_assessment_names=["Python (New)", "Java Programming"],
    )
    decision = RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="compare",
        confidence="HIGH",
        query_required=True,
        comparison_required=True,
        recommendation_required=False,
    )
    comparison_context = ComparisonContext(
        matched_assessments=[],
        unmatched_names=[],
        comparison_possible=False,
        reason="test",
    )

    state_extractor = MagicMock()
    state_extractor.extract.return_value = state
    router = MagicMock()
    router.route.return_value = decision
    query_builder = MagicMock()
    hybrid_retriever = MagicMock()
    comparison_pipeline = MagicMock()
    comparison_pipeline.run.return_value = comparison_context
    prompt_builder = MagicMock()
    prompt_builder.build.return_value = MagicMock(route=RouteType.COMPARE)
    response_generator = MagicMock()
    response_generator.generate.return_value = LLMGenerationResult(
        reply="Comparison unavailable.",
        recommended_names=[],
        end_of_conversation=False,
        provider="mock",
        model="mock",
        latency_ms=1.0,
        tokens_prompt=1,
        tokens_completion=1,
        tokens_total=2,
        finish_reason="stop",
    )
    response_validator = MagicMock()
    response_validator.validate.return_value = ValidatedGenerationResult(
        reply="Comparison unavailable.",
        validated_names=[],
        invalid_names=[],
        end_of_conversation=False,
        validation_passed=True,
        validation_errors=[],
    )
    response_builder = MagicMock()
    response_builder.build.return_value = ChatResponse(
        reply="Comparison unavailable.",
        recommendations=None,
    )

    service = ChatService(
        state_extractor=state_extractor,
        router=router,
        query_builder=query_builder,
        hybrid_retriever=hybrid_retriever,
        comparison_pipeline=comparison_pipeline,
        prompt_builder=prompt_builder,
        response_generator=response_generator,
        response_validator=response_validator,
        response_builder=response_builder,
    )

    service.chat([ConversationMessage(role="user", content="Compare Python and Java")])

    comparison_pipeline.run.assert_called_once_with(state, decision)
    hybrid_retriever.search.assert_not_called()
