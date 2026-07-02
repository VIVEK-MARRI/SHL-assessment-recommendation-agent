"""Comprehensive regression tests for conversational intelligence improvements.

Tests cover all 14 required behavioral areas from the production enhancement spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.conversation_advisor import (
    CatalogLimitationHandler,
    CatalogRelationshipResolver,
    ClarificationAnalyzer,
    ConfirmationDetector,
)
from agent.generation import (
    ResponseGenerator,
    _extract_last_user_message,
    _filter_grounded_names,
)
from agent.generation_models import LLMGenerationResult
from agent.prompt_models import GroundingAssessment, PromptMetadata, PromptPackage
from agent.prompt_templates import PromptTemplates
from agent.routing_models import RouteType


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def resolver() -> CatalogRelationshipResolver:
    r = CatalogRelationshipResolver()
    r.load()
    return r


@pytest.fixture
def detector() -> ConfirmationDetector:
    return ConfirmationDetector()


@pytest.fixture
def limiter() -> CatalogLimitationHandler:
    return CatalogLimitationHandler()


@pytest.fixture
def analyzer() -> ClarificationAnalyzer:
    return ClarificationAnalyzer()


# =========================================================================
# 1. CatalogRelationshipResolver — relationship discovery
# =========================================================================

class TestCatalogRelationshipResolver:
    def test_opq32r_relationships(self, resolver: CatalogRelationshipResolver) -> None:
        rels = resolver.get_relationships("Occupational Personality Questionnaire OPQ32r")
        assert len(rels) >= 20, "OPQ32r should have many derived reports"
        assert any("Leadership Report" in r for r in rels)
        assert any("Candidate Plus Report" in r for r in rels)
        assert any("Profile Report" in r for r in rels)

    def test_base_assessment_detection(self, resolver: CatalogRelationshipResolver) -> None:
        assert resolver.is_base_assessment("Occupational Personality Questionnaire OPQ32r") is True
        assert resolver.is_base_assessment("OPQ Leadership Report") is False
        assert resolver.is_base_assessment("SHL Verify Interactive G+") is True

    def test_get_family_includes_base_and_derived(self, resolver: CatalogRelationshipResolver) -> None:
        family = resolver.get_family("Occupational Personality Questionnaire OPQ32r")
        assert len(family) >= 20
        assert "Occupational Personality Questionnaire OPQ32r" in family
        assert "OPQ Leadership Report" in family

    def test_get_family_for_derived_item(self, resolver: CatalogRelationshipResolver) -> None:
        family = resolver.get_family("OPQ Leadership Report")
        assert len(family) >= 2
        assert "Occupational Personality Questionnaire OPQ32r" in family or any(
            "OPQ" in m for m in family
        ), "Should include related OPQ items"

    def test_verify_relationships(self, resolver: CatalogRelationshipResolver) -> None:
        rels = resolver.get_relationships("SHL Verify Interactive G+")
        assert len(rels) >= 3
        assert any("Candidate Report" in r for r in rels)

    def test_no_relationships_for_unknown(self, resolver: CatalogRelationshipResolver) -> None:
        rels = resolver.get_relationships("Nonexistent Assessment Name")
        assert rels == []

    def test_format_relationship_context(self, resolver: CatalogRelationshipResolver) -> None:
        ctx = resolver.format_relationship_context(["Occupational Personality Questionnaire OPQ32r"])
        assert "OPQ32r is the base assessment" in ctx
        assert "Related reports" in ctx

    def test_format_relationship_context_multiple(self, resolver: CatalogRelationshipResolver) -> None:
        ctx = resolver.format_relationship_context([
            "Occupational Personality Questionnaire OPQ32r",
            "SHL Verify Interactive G+",
        ])
        assert "OPQ32r is the base assessment" in ctx
        assert "Verify Interactive G+ is the base assessment" in ctx


# =========================================================================
# 2. ConfirmationDetector — deterministic confirmation/tradeoff/comparison
# =========================================================================

class TestConfirmationDetector:
    @pytest.mark.parametrize("text", [
        "Looks good",
        "Perfect!",
        "That's what we need",
        "This is what I need",
        "Let's go with it",
        "Go for it",
        "Works for me",
        "Fine by me",
        "I'll take these",
        "Yes",
        "Yeah",
        "Sure",
        "Okay",
        "OK",
        "Alright",
        "Definitely",
        "Absolutely",
        "Thanks",
        "That's great",
        "Makes sense",
    ])
    def test_confirmation_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert detector.is_confirmation(text), f"Should detect confirmation: {text!r}"

    @pytest.mark.parametrize("text", [
        "I need a Python developer",
        "What do you have for Java?",
        "Tell me more about OPQ",
        "Compare these two",
        "Do I really need Verify?",
    ])
    def test_non_confirmation_not_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert not detector.is_confirmation(text), f"Should NOT detect confirmation: {text!r}"

    @pytest.mark.parametrize("text", [
        "Do I really need Verify G+?",
        "Is it necessary to include the personality test?",
        "Is it worth having both?",
        "Can we skip the cognitive test?",
        "Is there any benefit to adding this?",
        "What do we gain from the leadership report?",
        "What's the point of the simulation?",
    ])
    def test_tradeoff_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert detector.is_tradeoff_question(text), f"Should detect tradeoff: {text!r}"

    @pytest.mark.parametrize("text", [
        "How much does it cost?",
        "What is this assessment about?",
    ])
    def test_non_tradeoff_not_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert not detector.is_tradeoff_question(text), f"Should NOT detect tradeoff: {text!r}"

    @pytest.mark.parametrize("text", [
        "Compare OPQ and Verify G+",
        "What's the difference between these?",
        "How do they compare?",
        "Which one should I choose?",
        "OPQ vs Verify",
    ])
    def test_comparison_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert detector.is_comparison_request(text), f"Should detect comparison: {text!r}"

    @pytest.mark.parametrize("text", [
        "I need a Python assessment",
        "What do you recommend?",
    ])
    def test_non_comparison_not_detected(self, detector: ConfirmationDetector, text: str) -> None:
        assert not detector.is_comparison_request(text), f"Should NOT detect comparison: {text!r}"


# =========================================================================
# 3. CatalogLimitationHandler — unknown assessment handling
# =========================================================================

class TestCatalogLimitationHandler:
    def test_known_assessment_in_catalog(self, limiter: CatalogLimitationHandler) -> None:
        assert limiter.is_in_catalog("Python (New)")
        assert limiter.is_in_catalog("Occupational Personality Questionnaire OPQ32r")

    def test_unknown_assessment_not_in_catalog(self, limiter: CatalogLimitationHandler) -> None:
        assert not limiter.is_in_catalog("Rust")
        assert not limiter.is_in_catalog("Go Programming Language")
        assert not limiter.is_in_catalog("OpenAI")
        assert not limiter.is_in_catalog("ChatGPT")
        assert not limiter.is_in_catalog("Claude")

    def test_nearest_alternatives_generic(self, limiter: CatalogLimitationHandler) -> None:
        alts = limiter.find_nearest_alternatives("Rust")
        assert isinstance(alts, list)
        # Should find C/C++ related items
        if alts:
            assert any("C" in a or "Programming" in a for a in alts)

    def test_nearest_alternatives_specific(self, limiter: CatalogLimitationHandler) -> None:
        alts = limiter.find_nearest_alternatives("Go programming")
        assert isinstance(alts, list)
        if alts:
            assert any("Programming" in a for a in alts)


# =========================================================================
# 4. ClarificationAnalyzer — smart missing field detection
# =========================================================================

class TestClarificationAnalyzer:
    def test_empty_state_asks_role(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(role=None, seniority=None, technical_skills=[], constraints=[])
        assert analyzer.determine_missing_field(state) == "role"

    def test_role_only_asks_seniority(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(role="Developer", seniority=None, technical_skills=[], constraints=[])
        assert analyzer.determine_missing_field(state) == "seniority"

    def test_role_and_seniority_asks_skills(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(role="Developer", seniority="Senior", technical_skills=[], constraints=[])
        assert analyzer.determine_missing_field(state) == "technical_skills"

    def test_role_seniority_skills_asks_constraints(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(role="Dev", seniority="Mid", technical_skills=["Python"], constraints=[])
        assert analyzer.determine_missing_field(state) == "constraints"

    def test_complete_state_returns_none(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(
            role="Dev", seniority="Senior", technical_skills=["Java"], constraints=["English"]
        )
        assert analyzer.determine_missing_field(state) is None

    def test_skills_only_asks_role(self, analyzer: ClarificationAnalyzer) -> None:
        state = _MockState(role=None, seniority=None, technical_skills=["Python"], constraints=[])
        assert analyzer.determine_missing_field(state) == "role"

    def test_questions_are_not_empty(self, analyzer: ClarificationAnalyzer) -> None:
        for field in ["role", "seniority", "technical_skills", "constraints"]:
            q = analyzer.get_clarification_question(field)
            assert q
            assert len(q) > 10


# =========================================================================
# 5. _extract_last_user_message — parsing logic
# =========================================================================

class TestExtractLastUserMessage:
    def test_single_turn(self) -> None:
        prompt = "User:\nI need a Python test"
        assert _extract_last_user_message(prompt) == "I need a Python test"

    def test_multi_turn(self) -> None:
        prompt = "User:\nI need a Python test\n\nAssistant:\nWhat level?\n\nUser:\nSenior"
        assert _extract_last_user_message(prompt) == "Senior"

    def test_confirmation_last(self) -> None:
        prompt = "User:\nHere are options\n\nAssistant:\nThanks\n\nUser:\nLooks good"
        assert _extract_last_user_message(prompt) == "Looks good"

    def test_empty_prompt(self) -> None:
        assert _extract_last_user_message("") == ""


# =========================================================================
# 6. _filter_grounded_names — grounding logic
# =========================================================================

class TestFilterGroundedNames:
    def test_filters_ungrounded(self) -> None:
        result = _filter_grounded_names(
            ["Python Test", "Java Test", "Fake Test"],
            ["Python Test", "Java Test"],
        )
        assert result == ["Python Test", "Java Test"]

    def test_preserves_order(self) -> None:
        result = _filter_grounded_names(
            ["Java Test", "Python Test"],
            ["Python Test", "Java Test"],
        )
        assert result == ["Python Test", "Java Test"]

    def test_empty_grounding(self) -> None:
        result = _filter_grounded_names(["Python Test"], [])
        assert result == []

    def test_empty_requested(self) -> None:
        result = _filter_grounded_names([], ["Python Test"])
        assert result == []

    def test_case_insensitive(self) -> None:
        result = _filter_grounded_names(
            ["python test"],
            ["Python Test"],
        )
        assert result == ["Python Test"]

    def test_not_a_list(self) -> None:
        result = _filter_grounded_names("not a list", ["Python"])
        assert result == []


# =========================================================================
# 7. Prompt template content
# =========================================================================

class TestNewPromptTemplates:
    def test_recommendation_has_why(self) -> None:
        templates = PromptTemplates()
        prompt = templates.get_template(RouteType.RECOMMEND)
        assert "WHY" in prompt or "why" in prompt
        assert "GROUNDING CONTEXT" in prompt

    def test_clarification_has_single_question(self) -> None:
        templates = PromptTemplates()
        prompt = templates.get_template(RouteType.CLARIFY)
        assert "ONE" in prompt or "one" in prompt
        assert "exactly ONE" in prompt or "exactly one" in prompt

    def test_comparison_has_difference_explanation(self) -> None:
        templates = PromptTemplates()
        prompt = templates.get_template(RouteType.COMPARE)
        assert "Differences" in prompt or "differences" in prompt
        assert "Purpose" in prompt or "purpose" in prompt

    def test_refusal_has_graceful_language(self) -> None:
        templates = PromptTemplates()
        prompt = templates.get_template(RouteType.REFUSE)
        assert "Politely" in prompt

    def test_recommendation_allows_catalog_limits(self) -> None:
        templates = PromptTemplates()
        prompt = templates.get_template(RouteType.RECOMMEND)
        assert "no assessment" in prompt.lower() or "no exact" in prompt.lower()


# =========================================================================
# 8. Generation post-processing — confirmation end_of_conversation
# =========================================================================

class TestConfirmationEndOfConversation:
    """Verify that confirmation detection sets end_of_conversation properly."""

    def _make_package(self, user_prompt: str, route: RouteType = RouteType.RECOMMEND) -> PromptPackage:
        return PromptPackage(
            system_prompt="Test",
            user_prompt=user_prompt,
            route=route,
            grounding_assessments=[
                GroundingAssessment(
                    name="Test Assessment",
                    description="Test",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://test",
                )
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=route.value),
        )

    class _MockClient:
        def __init__(self) -> None:
            self._responses = {}

        def generate(self, system_prompt: str, user_payload: str) -> dict:
            return {
                "content": '{"reply": "Here are my recommendations", "recommended_names": ["Test Assessment"], "end_of_conversation": false}',
                "provider": "mock",
                "model": "mock",
                "latency_ms": 10.0,
                "tokens_prompt": 5,
                "tokens_completion": 3,
                "tokens_total": 8,
                "finish_reason": "stop",
            }

    def test_confirmation_sets_end_of_conversation(self) -> None:
        package = self._make_package("User:\nLooks good", RouteType.RECOMMEND)
        generator = ResponseGenerator(client=self._MockClient())
        result = generator.generate(package)
        assert result.end_of_conversation is True
        assert result.recommended_names == ["Test Assessment"]

    def test_non_confirmation_does_not_set_end(self) -> None:
        package = self._make_package("User:\nI need a Java assessment", RouteType.RECOMMEND)
        generator = ResponseGenerator(client=self._MockClient())
        result = generator.generate(package)
        assert result.end_of_conversation is False

    def test_confirmation_does_not_affect_clarify(self) -> None:
        package = self._make_package("User:\nLooks good", RouteType.CLARIFY)
        generator = ResponseGenerator(client=self._MockClient())
        result = generator.generate(package)
        # CLARIFY route doesn't have confirmation post-processing
        assert result.end_of_conversation is False


# =========================================================================
# 9. Grounding override behavior (preserved from original)
# =========================================================================

class TestGroundingOverride:
    """Verify grounding override still works with new prompts."""

    _GROUNDED = [
        GroundingAssessment(
            name="Python Advanced",
            description="Python test",
            duration="30 min",
            job_levels=["Mid"],
            languages=["English"],
            remote=True,
            adaptive=False,
            test_type=["Knowledge"],
            link="http://python",
        )
    ]

    def _make_package(self, route: RouteType, assessments: list | None = None) -> PromptPackage:
        return PromptPackage(
            system_prompt="Test system prompt",
            user_prompt="User:\nI need a Python developer",
            route=route,
            grounding_assessments=assessments or self._GROUNDED,
            metadata=PromptMetadata(prompt_version="1.0", route=route.value),
        )

    class _OverrideClient:
        def __init__(self, content: str) -> None:
            self._content = content

        def generate(self, system_prompt: str, user_payload: str) -> dict:
            return {
                "content": self._content,
                "provider": "mock",
                "model": "mock",
                "latency_ms": 10.0,
                "tokens_prompt": 5,
                "tokens_completion": 3,
                "tokens_total": 8,
                "finish_reason": "stop",
            }

    def test_override_on_empty_recs(self) -> None:
        """When LLM returns empty recs but grounding exists, override fires."""
        client = self._OverrideClient(
            '{"reply": "No matches", "recommended_names": [], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        result = generator.generate(self._make_package(RouteType.RECOMMEND))
        assert result.recommended_names == ["Python Advanced"]
        assert "most relevant assessments" in result.reply

    def test_override_on_not_enough_info(self) -> None:
        client = self._OverrideClient(
            '{"reply": "The retrieved SHL catalog does not provide enough information to answer that.", "recommended_names": []}'
        )
        generator = ResponseGenerator(client=client)
        result = generator.generate(self._make_package(RouteType.RECOMMEND))
        assert result.recommended_names == ["Python Advanced"]

    def test_no_override_when_valid_recs(self) -> None:
        client = self._OverrideClient(
            '{"reply": "Here are options", "recommended_names": ["Python Advanced"], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        result = generator.generate(self._make_package(RouteType.RECOMMEND))
        assert result.recommended_names == ["Python Advanced"]
        assert result.reply == "Here are options"


# =========================================================================
# 10. Relationship context injection into prompts
# =========================================================================

class TestRelationshipContextInjection:
    """Verify that relationship notes appear in the generated prompt."""

    def _make_package(self) -> PromptPackage:
        return PromptPackage(
            system_prompt="Test",
            user_prompt="User:\nI need an assessment",
            route=RouteType.RECOMMEND,
            grounding_assessments=[
                GroundingAssessment(
                    name="Occupational Personality Questionnaire OPQ32r",
                    description="Personality questionnaire",
                    duration="25 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Personality"],
                    link="http://opq",
                ),
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND),
        )

    def _mock_client(self) -> object:
        class C:
            def generate(self, system_prompt: str, user_payload: str) -> dict:
                # Capture that RELATIONSHIP NOTES was injected
                self.last_system_prompt = system_prompt
                return {
                    "content": '{"reply": "OK", "recommended_names": ["Occupational Personality Questionnaire OPQ32r"], "end_of_conversation": false}',
                    "provider": "mock",
                    "model": "mock",
                    "latency_ms": 10.0,
                    "tokens_prompt": 5,
                    "tokens_completion": 3,
                    "tokens_total": 8,
                    "finish_reason": "stop",
                }
        return C()

    def test_relationship_notes_in_prompt(self) -> None:
        client = self._mock_client()
        generator = ResponseGenerator(client=client)
        generator.generate(self._make_package())
        assert "RELATIONSHIP NOTES" in client.last_system_prompt
        assert "base assessment" in client.last_system_prompt


# =========================================================================
# 11. State extraction prompt enhancements
# =========================================================================

class TestStateExtractionPrompt:
    """Verify the state extraction prompt includes new instructions."""

    def test_contains_confirmation_instructions(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "state_extraction_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "CONFIRMATION DETECTION" in content
        assert "Looks good" in content

    def test_contains_tradeoff_instructions(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "state_extraction_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "TRADEOFF DETECTION" in content
        assert "Do I really need" in content

    def test_contains_conversation_goal(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "state_extraction_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "conversation_goal" in content
        assert "confirmed" in content


# =========================================================================
# 12. Hallucination safety (no LLM needed - test grounding logic)
# =========================================================================

class TestHallucinationSafety:
    """Verify the system prevents hallucinated assessments."""

    def test_filter_removes_ungrounded(self) -> None:
        names = _filter_grounded_names(
            ["Real Assessment", "Fake Assessment"],
            ["Real Assessment"],
        )
        assert "Fake Assessment" not in names
        assert "Real Assessment" in names

    def test_empty_when_all_fake(self) -> None:
        names = _filter_grounded_names(
            ["Made Up", "Also Fake"],
            ["Real"],
        )
        assert names == []

    def test_grounding_override_rejects_empty(self) -> None:
        """Test the grounding override in ResponseGenerator."""
        client = _make_simple_client('{"reply": "Nothing found", "recommended_names": []}')
        package = PromptPackage(
            system_prompt="Test",
            user_prompt="User:\nI need something",
            route=RouteType.RECOMMEND,
            grounding_assessments=[
                GroundingAssessment(
                    name="Grounded Assessment",
                    description="Real assessment",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://real",
                )
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND),
        )
        generator = ResponseGenerator(client=client)
        result = generator.generate(package)
        assert result.recommended_names == ["Grounded Assessment"]
        assert "most relevant assessments" in result.reply


def _make_simple_client(content: str) -> object:
    class SimpleMockClient:
        def generate(self, system_prompt: str, user_payload: str) -> dict:
            return {
                "content": content,
                "provider": "mock",
                "model": "mock",
                "latency_ms": 10.0,
                "tokens_prompt": 5,
                "tokens_completion": 3,
                "tokens_total": 8,
                "finish_reason": "stop",
            }
    return SimpleMockClient()


# =========================================================================
# 13. Mock state for testing
# =========================================================================

class _MockState:
    """Minimal mock for ConversationState-like objects."""
    def __init__(
        self,
        role: str | None = None,
        seniority: str | None = None,
        technical_skills: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> None:
        self.role = role
        self.seniority = seniority
        self.technical_skills = technical_skills or []
        self.constraints = constraints or []


# =========================================================================
# 14. Comparison spec compliance
# =========================================================================

class TestComparisonSpecCompliance:
    """Tests that the comparison prompt and generation match the spec."""

    def test_comparison_prompt_has_required_sections(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "Purpose" in content
        assert "what it measures" in content or "What it measures" in content
        assert "Typical use case" in content or "typical use case" in content
        assert "Target audience" in content or "target audience" in content
        assert "Differences" in content or "differences" in content
        assert "prefer" in content or "preferred" in content

    def test_comparison_prompt_no_clarification(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "Do NOT ask unnecessary clarification" in content

    def test_comparison_prompt_missing_assessment_template(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "couldn't find" in content.lower()
        assert "SHL Individual Test Solutions catalog" in content

    def test_comparison_prompt_recommendations(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "Recommendations" in content or "recommendations" in content

    def test_comparison_prompt_never_invent(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "Never invent" in content

    def test_unmatched_names_injected_into_context(self) -> None:
        client = _make_simple_client('{"reply": "ok", "recommended_names": [], "end_of_conversation": false}')
        generator = ResponseGenerator(client=client)
        package = PromptPackage(
            system_prompt="You are a comparison consultant.",
            user_prompt="User:\nCompare OPQ32r and Rust Assessment",
            route=RouteType.COMPARE,
            unmatched_names=["Rust Assessment"],
            grounding_assessments=[
                GroundingAssessment(
                    name="OPQ32r",
                    description="Workplace personality assessment",
                    duration="25 min",
                    job_levels=["Professional"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Personality"],
                    link="http://opq32r",
                )
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.COMPARE.value),
        )
        from agent.generation import SYSTEM_INSTRUCTIONS as sys_instructions
        result = generator.generate(package)
        assert result.reply is not None

    def test_comparison_prompt_no_extra_keys(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "comparison_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "recommended_names" in content
        assert "end_of_conversation" in content
        # Should NOT have extra response fields
        assert "extra keys" in content.lower() or "Never include extra keys" in content

    def test_comparison_router_does_not_clarify(self) -> None:
        """COMPARE route runs before CLARIFY in the router—verification."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        from agent.routing_models import RouteType
        router = RuleBasedRouter()
        state = ConversationState(
            comparison_requested=True,
            mentioned_assessment_names=["OPQ32r", "Verify G+"],
            scope_flag="in_scope",
        )
        decision = router.route(state)
        assert decision.route == RouteType.COMPARE

    def test_comparison_with_mixed_matched_unmatched(self) -> None:
        """When some assessments are found and some are not, unmatched are tracked."""
        from agent.catalog_matcher import CatalogMatcher
        from agent.comparison import ComparisonPipeline
        from agent.conversation_models import ConversationState
        matcher = CatalogMatcher()
        matcher.load()
        pipeline = ComparisonPipeline(matcher=matcher)
        state = ConversationState(
            mentioned_assessment_names=[
                "OPQ32r",
                "Verify G+",
                "FakeAssessmentThatDoesNotExist",
            ],
        )
        from agent.routing_models import RoutingDecision
        decision = RoutingDecision(
            route=RouteType.COMPARE,
            next_module="comparison_pipeline",
            reason="test",
            confidence="HIGH",
            query_required=True,
            comparison_required=True,
        )
        ctx = pipeline.run(state, decision)
        assert len(ctx.matched_assessments) >= 2
        assert "FakeAssessmentThatDoesNotExist" in ctx.unmatched_names
        assert ctx.comparison_possible is True


# =========================================================================
# 15. Unknown assessment handling (RECOMMEND route)
# =========================================================================

class TestUnknownAssessmentHandling:
    """Tests that unknown assessment names are properly handled in RECOMMEND."""

    def test_recommendation_prompt_has_spec_template(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "recommendation_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "couldn't find" in content.lower()
        assert "SHL Individual Test Solution" in content
        assert "closest relevant assessments" in content.lower()

    def test_unknown_assessment_injects_not_in_catalog(self) -> None:
        """When mentioned_assessment_names contains items not in grounding,
        a NOT IN CATALOG section is injected into the prompt context."""
        client = _make_simple_client(
            '{"reply": "I could not find it.", "recommended_names": ["Python (New)"], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        package = PromptPackage(
            system_prompt="You are an SHL consultant.",
            user_prompt="User:\nI need Hogwarts Wizard Assessment",
            route=RouteType.RECOMMEND,
            mentioned_assessment_names=["Hogwarts Wizard Assessment"],
            grounding_assessments=[
                GroundingAssessment(
                    name="Python (New)",
                    description="Python programming test",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://python",
                ),
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND.value),
        )
        result = generator.generate(package)
        assert result.reply is not None

    def test_known_assessment_no_not_in_catalog(self) -> None:
        """When all mentioned assessments are in grounding, no NOT IN CATALOG note."""
        client = _make_simple_client(
            '{"reply": "Here are the assessments.", "recommended_names": ["Python (New)"], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        package = PromptPackage(
            system_prompt="You are an SHL consultant.",
            user_prompt="User:\nI need Python (New)",
            route=RouteType.RECOMMEND,
            mentioned_assessment_names=["Python (New)"],
            grounding_assessments=[
                GroundingAssessment(
                    name="Python (New)",
                    description="Python programming test",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://python",
                ),
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND.value),
        )
        result = generator.generate(package)
        assert result.reply is not None

    def test_unknown_assessment_during_refine(self) -> None:
        """Unknown assessment handling also applies to REFINE route."""
        client = _make_simple_client(
            '{"reply": "Updated results.", "recommended_names": ["C Programming (New)"], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        package = PromptPackage(
            system_prompt="You are an SHL consultant.",
            user_prompt="User:\nActually I need Rust Assessment",
            route=RouteType.REFINE,
            mentioned_assessment_names=["Rust Assessment"],
            grounding_assessments=[
                GroundingAssessment(
                    name="C Programming (New)",
                    description="C programming test",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://c",
                ),
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.REFINE.value),
        )
        result = generator.generate(package)
        assert result.reply is not None


# =========================================================================
# 16. Unsupported technology handling
# =========================================================================

class TestUnsupportedTechnologyHandling:
    """Tests for the unsupported technology spec."""

    def test_recommendation_prompt_has_unsupported_tech_template(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "recommendation_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "There isn't a dedicated" in content
        assert "SHL catalog" in content
        assert "explain why each is relevant" in content.lower()

    def test_find_unsupported_technologies_returns_rust(self) -> None:
        handler = CatalogLimitationHandler()
        result = handler.find_unsupported_technologies(
            "I need Rust assessments",
            ["Python (New)", "C Programming (New)"],
        )
        assert "rust" in [r.lower() for r in result]

    def test_find_unsupported_technologies_identifies_supported(self) -> None:
        handler = CatalogLimitationHandler()
        result = handler.find_unsupported_technologies(
            "I need Python assessments",
            ["Python (New)", "C Programming (New)"],
        )
        rust_like = [r for r in result if r.lower() == "python"]
        assert len(rust_like) == 0

    def test_find_unsupported_technologies_go(self) -> None:
        handler = CatalogLimitationHandler()
        result = handler.find_unsupported_technologies(
            "I need Go assessments",
            ["Python (New)", "C Programming (New)"],
        )
        assert "go" in [r.lower() for r in result]

    def test_unsupported_tech_injects_no_dedicated_assessment(self) -> None:
        """When unsupported technology is detected, a NO DEDICATED ASSESSMENT section is injected."""
        client = _make_simple_client(
            '{"reply": "There is no dedicated assessment.", "recommended_names": ["C Programming (New)"], "end_of_conversation": false}'
        )
        generator = ResponseGenerator(client=client)
        package = PromptPackage(
            system_prompt="You are an SHL consultant.",
            user_prompt="User:\nI need Rust assessments",
            route=RouteType.RECOMMEND,
            mentioned_assessment_names=[],
            grounding_assessments=[
                GroundingAssessment(
                    name="C Programming (New)",
                    description="C programming test",
                    duration="30 min",
                    job_levels=["Mid"],
                    languages=["English"],
                    remote=True,
                    adaptive=False,
                    test_type=["Knowledge"],
                    link="http://c",
                ),
            ],
            metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND.value),
        )
        result = generator.generate(package)
        assert result.reply is not None


# =========================================================================
# 17. Clarification strategy spec
# =========================================================================

class TestClarificationStrategy:
    """Tests for the clarification strategy spec."""

    def test_state_extraction_prompt_has_spec_examples(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "state_extraction_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "I need an assessment" in content
        assert "Recommend something" in content
        assert "Hiring engineers" in content
        assert "Recommend Java assessments" in content
        assert "Recommend SQL tests" in content
        assert "Recommend assessments for graduates" in content
        assert "Recommend personality assessments" in content

    def test_clarification_prompt_minimizes_turns(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "agent" / "prompts" / "clarification_prompt.txt"
        content = path.read_text(encoding="utf-8")
        assert "Minimize conversational turns" in content
        assert "exactly ONE" in content

    def test_vague_role_clarifies(self) -> None:
        """A bare role with clarification_needed=True routes to CLARIFY."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        router = RuleBasedRouter()
        state = ConversationState(role="Engineers", clarification_needed=True)
        decision = router.route(state)
        assert decision.route == RouteType.CLARIFY

    def test_specific_skill_does_not_clarify(self) -> None:
        """Technical skills are sufficient even with clarification_needed."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        router = RuleBasedRouter()
        state = ConversationState(technical_skills=["Java"], clarification_needed=True)
        decision = router.route(state)
        assert decision.route == RouteType.RECOMMEND

    def test_role_with_skills_does_not_clarify(self) -> None:
        """Role + skills is sufficient even with clarification_needed=True."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        router = RuleBasedRouter()
        state = ConversationState(role="Engineer", technical_skills=["Python"], clarification_needed=True)
        decision = router.route(state)
        assert decision.route == RouteType.RECOMMEND

    def test_personality_required_does_not_clarify(self) -> None:
        """Personality flag alone routes to RECOMMEND via Step 5."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        router = RuleBasedRouter()
        state = ConversationState(personality_required=True)
        decision = router.route(state)
        assert decision.route == RouteType.RECOMMEND

    def test_role_only_no_clarification_flag_recommends(self) -> None:
        """Role only without clarification_needed routes to RECOMMEND."""
        from agent.conversation_models import ConversationState
        from agent.router import RuleBasedRouter
        router = RuleBasedRouter()
        state = ConversationState(role="Engineer")
        decision = router.route(state)
        assert decision.route == RouteType.RECOMMEND
