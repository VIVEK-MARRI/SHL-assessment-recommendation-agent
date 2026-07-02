from __future__ import annotations

import logging
from time import perf_counter

from agent.response_catalog import ResponseCatalog, CatalogLookupError
from agent.response_models import ChatResponse, Recommendation
from agent.routing_models import RouteType, RoutingDecision
from agent.validator_models import ValidatedGenerationResult

logger = logging.getLogger(__name__)

_ROUTES_WITH_RECOMMENDATIONS = {RouteType.RECOMMEND, RouteType.REFINE, RouteType.COMPARE}
_MAX_RECOMMENDATIONS = 10


class ResponseBuilderError(Exception):
    """Base exception for Response Builder failures."""


class InvalidValidatedResult(ResponseBuilderError):
    """Raised when the validated result is structurally unusable."""


class ResponseBuilder:
    """Assembles the final ChatResponse from a ValidatedGenerationResult."""

    def __init__(self, catalog: ResponseCatalog | None = None) -> None:
        self._catalog = catalog or ResponseCatalog()

    def build(
        self,
        validated: ValidatedGenerationResult,
        decision: RoutingDecision,
    ) -> ChatResponse:
        """
        Build the final ChatResponse.

        - RECOMMEND / REFINE / COMPARE → recommendations = list[Recommendation]
        - CLARIFY / REFUSE → recommendations = null
        """
        started = perf_counter()
        route = decision.route

        # Rule 9: never modify reply
        reply = validated.reply

        if route in _ROUTES_WITH_RECOMMENDATIONS:
            recommendations = self._build_recommendations(validated.validated_names)
        else:
            # CLARIFY and REFUSE always return null
            recommendations = None

        elapsed_ms = (perf_counter() - started) * 1000
        rec_count = len(recommendations) if recommendations else 0

        logger.info(
            "ResponseBuilder completed: route=%s recommendations=%d latency_ms=%.2f",
            route.value,
            rec_count,
            elapsed_ms,
        )

        return ChatResponse(
            reply=reply,
            recommendations=recommendations,
            end_of_conversation=validated.end_of_conversation,
        )

    def _build_recommendations(
        self, validated_names: list[str]
    ) -> list[Recommendation] | None:
        """Inject URL and test_type from catalog. Preserves ordering. Max 10."""
        if not validated_names:
            # Never return an empty list — return null
            return None

        recs: list[Recommendation] = []
        for name in validated_names[:_MAX_RECOMMENDATIONS]:
            try:
                record = self._catalog.lookup(name)
            except CatalogLookupError as exc:
                logger.warning("Skipping recommendation — catalog lookup failed: %s", exc)
                continue

            recs.append(
                Recommendation(
                    name=record["name"],
                    url=record["url"],
                    test_type=record["test_type"],
                )
            )

        # Still null if nothing survived lookup
        return recs if recs else None
