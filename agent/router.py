import logging
from typing import Optional

from agent.routing_models import RoutingDecision, RouteType
from agent.conversation_models import ConversationState

logger = logging.getLogger(__name__)

class RoutingError(Exception):
    """Base exception for routing errors."""
    pass

class InvalidConversationState(RoutingError):
    """Raised when conversation state is invalid."""
    pass

class RuleBasedRouter:
    """Deterministically routes conversation state to the next action."""

    def route(self, state: ConversationState, previous_state: Optional[ConversationState] = None) -> RoutingDecision:
        if not isinstance(state, ConversationState):
            raise InvalidConversationState("Input must be a valid ConversationState instance.")
            
        logger.info(f"Routing state: scope_flag={state.scope_flag}, comparison={state.comparison_requested}, clarification={state.clarification_needed}")

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
            return decision

        # Step 3: CLARIFY
        if state.clarification_needed:
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
            return decision

        # Check for REFINE (updated requirements)
        # Note: we check if requirements changed from previous state
        is_updated = self._is_updated_requirements(state, previous_state)
        
        # Step 5 check (prioritized over 4 if updated)
        if is_updated:
            decision = RoutingDecision(
                route=RouteType.REFINE,
                next_module="query_builder",
                reason="Updated requirements detected.",
                confidence="HIGH",
                query_required=True,
                comparison_required=False,
                recommendation_required=True
            )
            logger.info(f"Selected route: {decision.route}, Reason: {decision.reason}")
            return decision

        # Step 4: RECOMMEND
        is_sufficient = self._is_sufficient_information(state)
        if is_sufficient:
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
            return decision
            
        # Fallback if it's neither sufficient nor updated
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
        return decision

    def _determine_clarification_field(self, state: ConversationState) -> str:
        """
        Priority:
        1. role
        2. seniority
        3. technical_skills
        4. leadership_required
        5. personality_required
        6. cognitive_required
        7. simulation_required
        8. constraints
        """
        if not state.role:
            return "role"
        if not state.seniority:
            return "seniority"
        if not state.technical_skills:
            return "technical_skills"
        if not state.leadership_required:
            return "leadership_required"
        if not state.personality_required:
            return "personality_required"
        if not state.cognitive_required:
            return "cognitive_required"
        if not state.simulation_required:
            return "simulation_required"
        if not state.constraints:
            return "constraints"
            
        return "role" # default fallback

    def _is_sufficient_information(self, state: ConversationState) -> bool:
        """Recommend only when role exists AND technical_skills not empty. Seniority optional."""
        return bool(state.role) and bool(state.technical_skills)
        
    def _is_updated_requirements(self, state: ConversationState, previous_state: Optional[ConversationState]) -> bool:
        if not previous_state:
            return False
            
        # Detect added constraints, removed skills, changed requirement, added simulations, removed personality, added leadership
        if set(state.constraints) != set(previous_state.constraints):
            return True
        if set(state.technical_skills) != set(previous_state.technical_skills):
            return True
        if set(state.soft_skills) != set(previous_state.soft_skills):
            return True
        if state.role != previous_state.role:
            return True
        if state.seniority != previous_state.seniority:
            return True
        if state.simulation_required != previous_state.simulation_required:
            return True
        if state.personality_required != previous_state.personality_required:
            return True
        if state.leadership_required != previous_state.leadership_required:
            return True
        if state.cognitive_required != previous_state.cognitive_required:
            return True
            
        return False
