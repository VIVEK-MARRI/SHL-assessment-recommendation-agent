"""Comparison Pipeline — orchestrates catalog resolution into a ComparisonContext.

Receives ConversationState + RoutingDecision.
Returns ComparisonContext ready for the Prompt Builder (Module 16).

No LLM.  No retrieval.  No Prompt Builder.  No FastAPI.
"""

from __future__ import annotations

import logging
from time import perf_counter

from agent.catalog_matcher import CatalogLoadError, CatalogMatcher
from agent.comparison_models import ComparisonContext
from agent.conversation_models import ConversationState
from agent.routing_models import RouteType, RoutingDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ComparisonError(Exception):
    """Base exception for Comparison Pipeline failures."""


class InvalidComparisonRequest(ComparisonError):
    """Raised when the routing decision or conversation state is not suitable
    for comparison."""


# ---------------------------------------------------------------------------
# ComparisonPipeline
# ---------------------------------------------------------------------------


class ComparisonPipeline:
    """Converts mentioned_assessment_names into a structured ComparisonContext."""

    def __init__(self, matcher: CatalogMatcher | None = None) -> None:
        self._matcher = matcher or CatalogMatcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        state: ConversationState,
        decision: RoutingDecision,
    ) -> ComparisonContext:
        """Resolve assessment names and build a ComparisonContext.

        Raises:
            InvalidComparisonRequest: if the state/decision is not a COMPARE route.
            ComparisonError: for any other pipeline failure.
        """
        if not isinstance(state, ConversationState):
            raise InvalidComparisonRequest("state must be a ConversationState instance.")
        if not isinstance(decision, RoutingDecision):
            raise InvalidComparisonRequest(
                "decision must be a RoutingDecision instance."
            )
        if decision.route != RouteType.COMPARE:
            raise InvalidComparisonRequest(
                f"ComparisonPipeline only handles COMPARE routes. "
                f"Got: {decision.route.value}"
            )

        started_at = perf_counter()
        logger.info(
            "ComparisonPipeline.run: names=%r",
            state.mentioned_assessment_names,
        )

        # Ensure catalog is loaded
        try:
            self._matcher.load()
        except CatalogLoadError as exc:
            raise ComparisonError(f"Cannot load catalog: {exc}") from exc

        # Resolve names — order preserved
        names = state.mentioned_assessment_names
        matched, unmatched = self._matcher.match_many(names)

        # Determine whether comparison is possible
        # Issue 3: If ANY named assessment is unmatched (not in catalog), comparison is NOT
        # possible — we must explicitly tell the user which names don't exist in the catalog.
        if unmatched:
            comparison_possible = False
            found_names = ", ".join(f"'{m.name}'" for m in matched) if matched else "none"
            not_found_names = ", ".join(f"'{u}'" for u in unmatched)
            reason = (
                f"The following assessment(s) do not appear in the SHL catalog: {not_found_names}. "
                f"Found in catalog: {found_names}. "
                "Please verify the name(s) or ask to compare with a closest available alternative."
            )
        elif len(matched) >= 2:
            comparison_possible = True
            reason = f"Found {len(matched)} assessments for comparison."
        elif len(matched) == 1:
            comparison_possible = False
            reason = (
                "Need at least two assessments to compare. "
                f"Only '{matched[0].name}' was found."
            )
        else:
            comparison_possible = False
            reason = "No assessments could be resolved from the catalog."

        context = ComparisonContext(
            matched_assessments=matched,
            unmatched_names=unmatched,
            comparison_possible=comparison_possible,
            reason=reason,
        )

        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "ComparisonContext built: matched=%d unmatched=%d possible=%s elapsed_ms=%.2f",
            len(matched),
            len(unmatched),
            comparison_possible,
            elapsed_ms,
        )
        return context
