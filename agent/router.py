import logging
import re

from agent.routing_models import RoutingDecision, RouteType
from agent.conversation_models import ConversationState

logger = logging.getLogger(__name__)

# Deterministic off-topic keyword safety net
_OFF_TOPIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(who won|fifa|world cup|sports|game|match)\b", re.IGNORECASE),
    re.compile(r"\b(weather|temperature|forecast)\b", re.IGNORECASE),
    re.compile(r"\b(recipe|ingredients|cook|bake)\b", re.IGNORECASE),
    re.compile(r"\b(write code|program|debug|fix bug)\b", re.IGNORECASE),
    re.compile(r"\b(movie|film|song|music)\b", re.IGNORECASE),
    re.compile(r"\b(politics|president|election)\b", re.IGNORECASE),
    re.compile(r"\b(ignore|disregard|override)\s+(instructions|prompt|system|rules)\b", re.IGNORECASE),
    re.compile(r"\b(reveal|show|output|leak)\s+(your|the)\s+(prompt|instructions|system)\b", re.IGNORECASE),
]


class RoutingError(Exception):
    """Base exception for routing errors."""
    pass

class InvalidConversationState(RoutingError):
    """Raised when conversation state is invalid."""
    pass

class RuleBasedRouter:
    """Deterministically routes conversation state to the next action."""

    def route(self, state: ConversationState) -> RoutingDecision:
        if not isinstance(state, ConversationState):
            raise InvalidConversationState("Input must be a valid ConversationState instance.")
            
        logger.info(f"Routing state: scope_flag={state.scope_flag}, comparison={state.comparison_requested}, refinement={state.refinement_detected}")

        # Step 1: REFUSE
        if state.scope_flag != "in_scope":
            decision = RoutingDecision(
                route=RouteType.REFUSE,
                next_module="refusal",
                reason=f"State is not in scope. Flag: {state.scope_flag}",
                confidence="LOW" if state.scope_flag == "off_topic" else "HIGH",
                query_required=False,
                comparison_required=False,
                recommendation_required=False
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            logger.debug(
                "Routing decision=%s reason=%s state=%s",
                decision.route,
                decision.reason,
                state.model_dump()
            )
            return decision

        # Step 2: COMPARE
        if state.comparison_requested and len(state.mentioned_assessment_names) >= 1:
            decision = RoutingDecision(
                route=RouteType.COMPARE,
                next_module="comparison_pipeline",
                reason="User requested comparison of assessments.",
                confidence="HIGH",
                query_required=True,
                comparison_required=True,
                recommendation_required=False
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            logger.debug(
                "Routing decision=%s reason=%s state=%s",
                decision.route,
                decision.reason,
                state.model_dump()
            )
            return decision

        # Step 3: CLARIFY only when the state lacks a useful retrieval signal.
        if state.clarification_needed and not self._is_sufficient_information(state):
            clarification_field = self._determine_clarification_field(state)
            decision = RoutingDecision(
                route=RouteType.CLARIFY,
                next_module="clarification",
                reason=f"Need clarification on {clarification_field}.",
                confidence="MEDIUM",
                clarification_field=clarification_field,
                query_required=False,
                comparison_required=False,
                recommendation_required=False
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            logger.debug(
                "Routing decision=%s reason=%s state=%s",
                decision.route,
                decision.reason,
                state.model_dump()
            )
            return decision

        # Step 4: REFINE when the state extraction detected a change
        if state.refinement_detected:
            decision = RoutingDecision(
                route=RouteType.REFINE,
                next_module="query_builder",
                reason="Updated requirements detected via state extraction.",
                confidence="HIGH",
                query_required=True,
                comparison_required=False,
                recommendation_required=True
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            logger.debug(
                "Routing decision=%s reason=%s state=%s",
                decision.route,
                decision.reason,
                state.model_dump()
            )
            return decision

        # Step 5: RECOMMEND
        if self._is_sufficient_information(state):
            decision = RoutingDecision(
                route=RouteType.RECOMMEND,
                next_module="query_builder",
                reason="Sufficient information provided for recommendation.",
                confidence="HIGH",
                query_required=True,
                comparison_required=False,
                recommendation_required=True
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            logger.debug(
                "Routing decision=%s reason=%s state=%s",
                decision.route,
                decision.reason,
                state.model_dump()
            )
            return decision
            
        # Fallback: CLARIFY
        clarification_field = self._determine_clarification_field(state)
        decision = RoutingDecision(
            route=RouteType.CLARIFY,
            next_module="clarification",
            reason=f"Need clarification on {clarification_field}.",
            confidence="MEDIUM",
            clarification_field=clarification_field,
            query_required=False,
            comparison_required=False,
            recommendation_required=False
        )
        logger.info(f"Selected fallback route: {decision.route}, Reason: {decision.reason}")
        logger.debug(
            "Routing decision=%s reason=%s state=%s",
            decision.route,
            decision.reason,
            state.model_dump()
        )
        return decision

    @staticmethod
    def contains_off_topic_pattern(text: str) -> bool:
        """Check if text matches off-topic patterns as a deterministic safety net."""
        return any(pattern.search(text) for pattern in _OFF_TOPIC_PATTERNS)

    def _determine_clarification_field(self, state: ConversationState) -> str:
        if not state.role:
            return "role"
        if not state.seniority:
            return "seniority"
        if not state.technical_skills:
            return "technical_skills"
        if not state.constraints:
            return "constraints"
        return "role"

    @staticmethod
    def _is_sufficient_information(state: ConversationState) -> bool:
        return bool(state.role) or bool(state.technical_skills)
