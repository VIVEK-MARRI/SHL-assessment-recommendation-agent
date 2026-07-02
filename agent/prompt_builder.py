from __future__ import annotations

import datetime
import logging
from time import perf_counter

from agent.comparison_models import ComparisonContext
from agent.conversation_models import ConversationMessage, ConversationState
from agent.prompt_models import GroundingAssessment, PromptMetadata, PromptPackage
from agent.prompt_templates import PromptTemplates, TemplateLoadError
from agent.routing_models import RouteType, RoutingDecision
from retrieval.retrieval_models import RetrievedAssessment

logger = logging.getLogger(__name__)

class PromptBuilderError(Exception):
    """Base exception for Prompt Builder failures."""

class InvalidPromptRoute(PromptBuilderError):
    """Raised when an invalid route is requested."""

class MissingGroundingContext(PromptBuilderError):
    """Raised when grounding context is required but missing."""


class PromptBuilder:
    """Combines conversation history, state, route, and grounding data into a final prompt."""

    def __init__(self, templates: PromptTemplates | None = None) -> None:
        self._templates = templates or PromptTemplates()

    def build(
        self,
        conversation: list[ConversationMessage],
        state: ConversationState,
        decision: RoutingDecision,
        retrieved_assessments: list[RetrievedAssessment] | None = None,
        comparison_context: ComparisonContext | None = None,
    ) -> PromptPackage:
        """Build the PromptPackage based on the routing decision."""
        started_at = perf_counter()
        
        # Determine the effective route. REFINE uses the RECOMMEND template.
        route = decision.route
        if route == RouteType.REFINE:
            template_route = RouteType.RECOMMEND
        else:
            template_route = route

        try:
            system_prompt = self._templates.get_template(template_route)
        except TemplateLoadError as e:
            raise PromptBuilderError(f"Failed to load prompt template: {e}") from e

        # Construct user prompt from history
        user_prompt_parts = []
        for msg in conversation:
            role = "User" if msg.role == "user" else "Assistant"
            user_prompt_parts.append(f"{role}:\n{msg.content}")
        user_prompt = "\n\n".join(user_prompt_parts)

        grounding: list[GroundingAssessment] = []
        
        if template_route == RouteType.RECOMMEND:
            if retrieved_assessments is None:
                raise MissingGroundingContext("retrieved_assessments required for RECOMMEND route.")
            # Top 8 unique, preserve order
            seen_ids = set()
            for rec in retrieved_assessments:
                if len(grounding) >= 8:
                    break
                if rec.entity_id not in seen_ids:
                    seen_ids.add(rec.entity_id)
                    grounding.append(
                        GroundingAssessment(
                            name=rec.name,
                            description=getattr(rec, "description", ""),  # fallback if missing
                            duration=rec.duration,
                            job_levels=rec.job_levels,
                            languages=rec.languages,
                            remote=rec.remote,
                            adaptive=rec.adaptive,
                            test_type=[rec.test_type] if rec.test_type else [],
                            link=rec.url,
                        )
                    )
        elif template_route == RouteType.COMPARE:
            if comparison_context is None:
                raise MissingGroundingContext("comparison_context required for COMPARE route.")
            seen_ids = set()
            for rec in comparison_context.matched_assessments:
                if len(grounding) >= 8:
                    break
                if rec.entity_id not in seen_ids:
                    seen_ids.add(rec.entity_id)
                    grounding.append(
                        GroundingAssessment(
                            name=rec.name,
                            description=rec.description,
                            duration=rec.duration,
                            job_levels=rec.job_levels,
                            languages=rec.languages,
                            remote=rec.remote,
                            adaptive=rec.adaptive,
                            test_type=rec.test_type,
                            link=rec.url,
                        )
                    )
        elif template_route in (RouteType.CLARIFY, RouteType.REFUSE):
            pass # No assessments
        else:
            raise InvalidPromptRoute(f"Unhandled route for PromptBuilder: {template_route}")

        metadata = PromptMetadata(
            prompt_version="1.0",
            route=route.value,
            assessment_count=len(grounding),
            conversation_turns=len(conversation),
            generated_at=datetime.datetime.now(datetime.UTC).isoformat()
        )

        package = PromptPackage(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            route=route,
            grounding_assessments=grounding,
            unmatched_names=(
                comparison_context.unmatched_names
                if template_route == RouteType.COMPARE and comparison_context is not None
                else []
            ),
            metadata=metadata
        )

        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "Prompt built: route=%s assessments=%d turns=%d latency=%.2fms",
            route.value, len(grounding), len(conversation), elapsed_ms
        )

        return package
