"""ChatService — the single orchestrator for the full recommendation pipeline."""

from __future__ import annotations

import logging
from time import perf_counter

from agent.comparison import ComparisonPipeline
from agent.conversation_models import ConversationMessage
from agent.generation import ResponseGenerator
from agent.prompt_builder import PromptBuilder
from agent.response_builder import ResponseBuilder
from agent.response_models import ChatResponse
from agent.router import RuleBasedRouter
from agent.routing_models import RouteType
from agent.state_extraction import StateExtractor
from agent.validator import ResponseValidator
from agent.query_builder import QueryBuilder
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.metadata_reranker import MetadataReranker, PENALTY_UNRELATED_TECH

logger = logging.getLogger(__name__)

_RETRIEVAL_ROUTES = {RouteType.RECOMMEND, RouteType.REFINE}
_COMPARISON_ROUTES = {RouteType.COMPARE}


class ChatServiceError(Exception):
    """Raised when the chat service pipeline fails."""


class ChatService:
    """Orchestrates the full pipeline from conversation messages to ChatResponse."""

    def __init__(
        self,
        state_extractor: StateExtractor,
        router: RuleBasedRouter,
        query_builder: QueryBuilder,
        hybrid_retriever: HybridRetriever,
        comparison_pipeline: ComparisonPipeline,
        prompt_builder: PromptBuilder,
        response_generator: ResponseGenerator,
        response_validator: ResponseValidator,
        response_builder: ResponseBuilder,
    ) -> None:
        self._state_extractor = state_extractor
        self._router = router
        self._query_builder = query_builder
        self._hybrid_retriever = hybrid_retriever
        self._comparison_pipeline = comparison_pipeline
        self._prompt_builder = prompt_builder
        self._response_generator = response_generator
        self._response_validator = response_validator
        self._response_builder = response_builder

    def chat(self, messages: list[ConversationMessage]) -> ChatResponse:
        """Run the full pipeline and return a ChatResponse."""
        started = perf_counter()

        # 1. Extract conversation state (LLM call #1)
        state = self._state_extractor.extract(messages)
        logger.info("State extracted: route_hint=%s", state.scope_flag)

        # 2. Route
        decision = self._router.route(state)
        logger.info("Route decided: %s (confidence=%s)", decision.route, decision.confidence)

        retrieved_assessments = None
        comparison_context = None

        # 3a. Retrieval pipeline for RECOMMEND / REFINE
        if decision.route in _RETRIEVAL_ROUTES:
            retrieval_query = self._query_builder.build(state=state, decision=decision)
            hybrid_result = self._hybrid_retriever.search(
                query=retrieval_query.query_text,
                state=state,
                filters=retrieval_query.filters,
                top_k=20,
            )
            
            # Deterministic post-retrieval filter for explicit technology mismatches
            filtered_assessments = []
            for assessment in hybrid_result.results:
                penalty = MetadataReranker._calculate_technology_penalty(
                    assessment, state.technical_skills, state.role
                )
                if penalty < PENALTY_UNRELATED_TECH:
                    filtered_assessments.append(assessment)
                else:
                    logger.info("Filtered out unrelated technology: %s", assessment.name)
            
            retrieved_assessments = filtered_assessments
            logger.info("Retrieved %d assessments (after technology filter).", len(retrieved_assessments))

        # 3b. Comparison pipeline for COMPARE
        elif decision.route in _COMPARISON_ROUTES:
            comparison_context = self._comparison_pipeline.run(state, decision)
            logger.info(
                "Comparison context: possible=%s", comparison_context.comparison_possible
            )

        # 4. Prompt Builder
        package = self._prompt_builder.build(
            conversation=messages,
            state=state,
            decision=decision,
            retrieved_assessments=retrieved_assessments,
            comparison_context=comparison_context,
        )

        # 5. LLM Generation (LLM call #2)
        raw_result = self._response_generator.generate(package)

        # 6. Validate
        validated = self._response_validator.validate(raw_result)

        # 7. Build final response
        response = self._response_builder.build(validated=validated, decision=decision)

        elapsed_ms = (perf_counter() - started) * 1000
        logger.info(
            "ChatService completed: route=%s latency_ms=%.2f",
            decision.route.value,
            elapsed_ms,
        )

        return response
