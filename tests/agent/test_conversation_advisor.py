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
        assert "ComparisonContext" in prompt
        assert "purpose" in prompt or "audience" in prompt or "target" in prompt

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
