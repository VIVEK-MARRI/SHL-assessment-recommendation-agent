"""Rule-based, fully deterministic Query Builder.

Converts a validated ConversationState + RoutingDecision into a
RetrievalQuery ready for the Hybrid Retriever.

No LLM.  No retrieval.  No catalog lookup.  No FastAPI.
"""

from __future__ import annotations

import logging
import re
from time import perf_counter

from agent.conversation_models import ConversationState
from agent.query_expansion import get_role_expansion, normalise_skills
from agent.query_models import QueryFilters, RetrievalQuery
from agent.routing_models import RouteType, RoutingDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class QueryBuilderError(Exception):
    """Base exception for Query Builder failures."""


class InvalidRoutingDecision(QueryBuilderError):
    """Raised when the RoutingDecision is not actionable by the Query Builder."""


class InvalidConversationState(QueryBuilderError):
    """Raised when the ConversationState cannot produce a valid query."""


# ---------------------------------------------------------------------------
# Duration extraction
# ---------------------------------------------------------------------------

_DURATION_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    # "1 hour", "2 hours"
    (re.compile(r"(\d+(?:\.\d+)?)\s*hours?", re.IGNORECASE), 60),
    # "90 minutes", "30 min"
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?)", re.IGNORECASE), 1),
]


def _extract_duration_minutes(constraints: list[str]) -> int | None:
    """Parse a maximum duration from free-text constraint strings."""
    for text in constraints:
        for pattern, multiplier in _DURATION_PATTERNS:
            match = pattern.search(text)
            if match:
                value = float(match.group(1))
                return int(value * multiplier)
    return None


# ---------------------------------------------------------------------------
# Job level mapping
# ---------------------------------------------------------------------------

_SENIORITY_TO_JOB_LEVELS: dict[str, list[str]] = {
    "intern": ["Entry Level"],
    "graduate": ["Graduate"],
    "junior": ["Professional Individual Contributor"],
    "mid": ["Professional Individual Contributor"],
    "senior": ["Manager"],
    "lead": ["Manager"],
    "director": ["Director"],
    "executive": ["Executive"],
    "vp": ["Executive"],
    "head": ["Manager", "Director"],
    "staff": ["Professional Individual Contributor"],
    "principal": ["Manager"],
}


def _map_seniority_to_job_levels(seniority: str | None) -> list[str]:
    """Return canonical job level strings for a seniority token."""
    if not seniority:
        return []
    key = seniority.strip().lower()
    # Exact match first
    if key in _SENIORITY_TO_JOB_LEVELS:
        return list(_SENIORITY_TO_JOB_LEVELS[key])
    # Partial match (e.g. "senior software engineer" → "senior")
    for token, levels in _SENIORITY_TO_JOB_LEVELS.items():
        if token in key:
            return list(levels)
    return []


# ---------------------------------------------------------------------------
# Test-type expansion
# ---------------------------------------------------------------------------

_TEST_TYPE_KNOWLEDGE = "Knowledge & Skills"
_TEST_TYPE_PERSONALITY = "Personality & Behavior"
_TEST_TYPE_ABILITY = "Ability & Aptitude"
_TEST_TYPE_SIMULATION = "Simulations"


def _build_test_types(state: ConversationState, excluded: set[str]) -> list[str]:
    """Determine which test types to request, respecting negative constraints."""
    types: list[str] = []

    if state.technical_skills and _TEST_TYPE_KNOWLEDGE not in excluded:
        types.append(_TEST_TYPE_KNOWLEDGE)

    if state.personality_required and _TEST_TYPE_PERSONALITY not in excluded:
        types.append(_TEST_TYPE_PERSONALITY)

    if state.cognitive_required and _TEST_TYPE_ABILITY not in excluded:
        types.append(_TEST_TYPE_ABILITY)

    if state.simulation_required and _TEST_TYPE_SIMULATION not in excluded:
        types.append(_TEST_TYPE_SIMULATION)

    return types


# ---------------------------------------------------------------------------
# Excluded-term detection
# ---------------------------------------------------------------------------

_EXCLUDE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bno\s+personality\b", re.IGNORECASE), "Personality"),
    (re.compile(r"\bno\s+simulation\b", re.IGNORECASE), "Simulation"),
    (re.compile(r"\bno\s+opq\b", re.IGNORECASE), "OPQ"),
    (re.compile(r"\bdo\s+not\s+(?:recommend|include)\s+opq\b", re.IGNORECASE), "OPQ"),
    (re.compile(r"\bwithout\s+personality\b", re.IGNORECASE), "Personality"),
    (re.compile(r"\bwithout\s+simulation\b", re.IGNORECASE), "Simulation"),
    (re.compile(r"\bexclude\s+opq\b", re.IGNORECASE), "OPQ"),
]


def _extract_excluded_terms(constraints: list[str]) -> list[str]:
    """Scan constraint strings and return explicitly excluded terms."""
    excluded: list[str] = []
    seen: set[str] = set()
    for text in constraints:
        for pattern, term in _EXCLUDE_PATTERNS:
            if pattern.search(text) and term not in seen:
                excluded.append(term)
                seen.add(term)
    return excluded


def _excluded_test_types(excluded_terms: list[str]) -> set[str]:
    """Convert excluded term labels to test-type canonical strings."""
    mapping = {
        "Personality": _TEST_TYPE_PERSONALITY,
        "Simulation": _TEST_TYPE_SIMULATION,
    }
    result: set[str] = set()
    for term in excluded_terms:
        canonical = mapping.get(term)
        if canonical:
            result.add(canonical)
    return result


# ---------------------------------------------------------------------------
# Token deduplication helper
# ---------------------------------------------------------------------------


def _dedup_ordered(tokens: list[str]) -> list[str]:
    """Deduplicate a token list preserving insertion order (case-insensitive key)."""
    seen: set[str] = set()
    result: list[str] = []
    for tok in tokens:
        key = tok.casefold()
        if key and key not in seen:
            seen.add(key)
            result.append(tok)
    return result


# ---------------------------------------------------------------------------
# Query Builder
# ---------------------------------------------------------------------------


class QueryBuilder:
    """Converts ConversationState + RoutingDecision into a RetrievalQuery."""

    _ACTIONABLE_ROUTES: frozenset[RouteType] = frozenset(
        {RouteType.RECOMMEND, RouteType.REFINE, RouteType.COMPARE}
    )

    def build(
        self,
        state: ConversationState,
        decision: RoutingDecision,
    ) -> RetrievalQuery:
        """Build and return a deterministic RetrievalQuery."""
        if not isinstance(state, ConversationState):
            raise InvalidConversationState(
                "state must be a ConversationState instance."
            )
        if not isinstance(decision, RoutingDecision):
            raise InvalidRoutingDecision(
                "decision must be a RoutingDecision instance."
            )
        if decision.route not in self._ACTIONABLE_ROUTES:
            raise InvalidRoutingDecision(
                f"QueryBuilder cannot handle route '{decision.route}'. "
                f"Actionable routes: {[r.value for r in self._ACTIONABLE_ROUTES]}"
            )

        started_at = perf_counter()
        logger.info(
            "QueryBuilder.build: role=%r seniority=%r route=%s",
            state.role,
            state.seniority,
            decision.route.value,
        )

        # --- Role expansion ------------------------------------------------
        expansion_terms = get_role_expansion(state.role or "")
        logger.info("Role expansion: role=%r terms=%r", state.role, expansion_terms)

        # --- Skill normalisation -------------------------------------------
        normalised_skills = normalise_skills(state.technical_skills)
        normalised_soft = normalise_skills(state.soft_skills)
        logger.info("Normalised technical skills: %r", normalised_skills)

        # --- Excluded terms ------------------------------------------------
        excluded_terms = _extract_excluded_terms(state.constraints)
        excluded_type_set = _excluded_test_types(excluded_terms)
        logger.info("Excluded terms: %r", excluded_terms)

        # --- Filters -------------------------------------------------------
        job_levels = _map_seniority_to_job_levels(state.seniority)
        languages = ["English"]           # default; extend here if needed
        max_duration = _extract_duration_minutes(state.constraints)
        test_types = _build_test_types(state, excluded_type_set)
        logger.info(
            "Filters: job_levels=%r languages=%r max_duration=%r test_types=%r",
            job_levels, languages, max_duration, test_types,
        )

        query_filters = QueryFilters(
            job_levels=job_levels,
            languages=languages,
            maximum_duration_minutes=max_duration,
            remote_only=None,
            adaptive_only=None,
            test_types=test_types,
        )

        # --- Required terms ------------------------------------------------
        required_parts: list[str] = []
        if state.role:
            required_parts.append(state.role)
        required_parts.extend(normalised_skills)
        required_terms = _dedup_ordered(required_parts)

        # --- Optional terms ------------------------------------------------
        optional_parts: list[str] = []
        optional_parts.extend(normalised_soft)
        optional_parts.extend(expansion_terms)
        if state.leadership_required:
            optional_parts.append("leadership")
        if state.cognitive_required:
            optional_parts.append("cognitive")
            optional_parts.append("reasoning")
        if state.simulation_required:
            optional_parts.append("simulation")
        if state.personality_required:
            optional_parts.append("personality")
        optional_terms = _dedup_ordered(optional_parts)

        # --- Query text & tokens ------------------------------------------
        # Build deterministic query_text: role + skills + soft skills +
        # constraints (non-excluded) + expansion
        text_parts: list[str] = []
        if state.role:
            text_parts.append(state.role)
        text_parts.extend(normalised_skills)
        text_parts.extend(normalised_soft)
        # Add constraints that are not purely negative filters
        for constraint in state.constraints:
            if not any(p.search(constraint) for p, _ in _EXCLUDE_PATTERNS):
                text_parts.append(constraint)
        text_parts.extend(expansion_terms)

        query_tokens = _dedup_ordered(text_parts)
        query_text = " ".join(query_tokens)

        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.info("Final query_text: %r  elapsed_ms=%.2f", query_text, elapsed_ms)

        return RetrievalQuery(
            query_text=query_text,
            query_tokens=query_tokens,
            required_terms=required_terms,
            optional_terms=optional_terms,
            excluded_terms=excluded_terms,
            filters=query_filters,
            expansion_terms=expansion_terms,
        )
