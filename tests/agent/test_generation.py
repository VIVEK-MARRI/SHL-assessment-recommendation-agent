import pytest

from agent.generation import ResponseGenerator
from agent.generation_client import (
    GenerationClient,
    GenerationTimeoutError,
    JSONGenerationError,
    ProviderError,
    RateLimitError,
)
from agent.generation_models import LLMGenerationResult
from agent.prompt_models import GroundingAssessment, PromptMetadata, PromptPackage
from agent.routing_models import RouteType


class MockGenerationClient(GenerationClient):
    def __init__(self, responses: list[dict | Exception]):
        from agent.llm_client import LLMClientConfig
        super().__init__(config=LLMClientConfig(provider="mock", api_key="mock", model="mock"))
        self.responses = responses
        self.call_count = 0
        self.last_system_prompt = ""
        self.last_user_payload = ""

    def generate(self, system_prompt: str, user_payload: str) -> dict:
        self.last_system_prompt = system_prompt
        self.last_user_payload = user_payload
        if self.call_count >= len(self.responses):
            raise Exception("No more mock responses available")
        
        response = self.responses[self.call_count]
        self.call_count += 1
        
        if isinstance(response, Exception):
            raise response
            
        return {
            "content": response.get("content", "{}"),
            "provider": "mock",
            "model": "mock-model",
            "latency_ms": 100.0,
            "tokens_prompt": 10,
            "tokens_completion": 5,
            "tokens_total": 15,
            "finish_reason": "stop",
        }


@pytest.fixture
def package() -> PromptPackage:
    return PromptPackage(
        system_prompt="Base system prompt",
        user_prompt="User input",
        route=RouteType.RECOMMEND,
        grounding_assessments=[
            GroundingAssessment(
                name="Assessment A",
                description="Desc A",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://a"
            )
        ],
        metadata=PromptMetadata(
            prompt_version="1.0",
            route=RouteType.RECOMMEND,
            assessment_count=1,
            conversation_turns=1
        )
    )


def test_generation_success(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": '{"reply": "Here is A", "recommended_names": ["Assessment A"], "end_of_conversation": true}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    
    assert isinstance(result, LLMGenerationResult)
    assert result.reply == "Here is A"
    assert result.recommended_names == ["Assessment A"]
    assert result.end_of_conversation is True
    
    assert "Base system prompt" in client.last_system_prompt
    assert "Assessment A" in client.last_system_prompt
    assert "Return ONLY valid JSON." in client.last_system_prompt
    assert "User input" in client.last_user_payload


def test_generation_markdown_json() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        {"content": '```json\n{"reply": "Hello", "recommended_names": []}\n```'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.reply == "Hello"


def test_generation_retry_success_on_malformed_json() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        {"content": 'Oops this is not JSON'},
        {"content": '{"reply": "Now it is JSON", "recommended_names": []}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.reply == "Now it is JSON"
    assert client.call_count == 2


def test_generation_retry_failure(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": 'Not JSON'},
        {"content": 'Still not JSON'}
    ])
    generator = ResponseGenerator(client=client)
    
    with pytest.raises(JSONGenerationError):
        generator.generate(package)
    assert client.call_count == 2


def test_generation_retry_success_on_rate_limit() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        RateLimitError("429"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.reply == "Success"
    assert client.call_count == 2


def test_generation_timeout_retry() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        GenerationTimeoutError("timeout"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.reply == "Success"
    assert client.call_count == 2


def test_generation_provider_error_503_retry() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        ProviderError("LLM request failed: 503 Service Unavailable"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.reply == "Success"
    assert client.call_count == 2


def test_generation_provider_error_400_no_retry(package: PromptPackage) -> None:
    client = MockGenerationClient([
        ProviderError("LLM client error 400: Bad Request")
    ])
    generator = ResponseGenerator(client=client)
    
    with pytest.raises(ProviderError):
        generator.generate(package)
    assert client.call_count == 1


def test_generation_unknown_fields(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": '{"reply": "Success", "recommended_names": [], "end_of_conversation": false, "extra": 123}'},
        {"content": '{"reply": "Success", "recommended_names": [], "end_of_conversation": false, "extra": 123}'}
    ])
    generator = ResponseGenerator(client=client)
    
    with pytest.raises(JSONGenerationError) as excinfo:
        generator.generate(package)
    assert "extra fields" in str(excinfo.value)
    assert client.call_count == 2


def test_generation_empty_recommendations() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.CLARIFY,
        grounding_assessments=[],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.CLARIFY),
    )
    client = MockGenerationClient([
        {"content": '{"reply": "No matches", "recommended_names": [], "end_of_conversation": false}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(pkg)
    assert result.recommended_names == []


def test_generation_filters_recommendations_to_grounding_context(package: PromptPackage) -> None:
    package.grounding_assessments.append(
        GroundingAssessment(
            name="Assessment B",
            description="Desc B",
            duration="45 min",
            job_levels=["Mid"],
            languages=["English"],
            remote=True,
            adaptive=False,
            test_type=["Knowledge"],
            link="http://b",
        )
    )
    client = MockGenerationClient([
        {
            "content": (
                '{"reply": "Here are options", '
                '"recommended_names": ["Catalog Valid But Ungrounded", "Assessment B", "Assessment A"], '
                '"end_of_conversation": true}'
            )
        }
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(package)

    assert result.recommended_names == ["Assessment A", "Assessment B"]


def test_generation_no_context_clarify(package: PromptPackage) -> None:
    package.route = RouteType.CLARIFY
    package.grounding_assessments = []
    
    client = MockGenerationClient([
        {"content": '{"reply": "What level?", "recommended_names": [], "end_of_conversation": false}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    assert result.reply == "What level?"
    assert "GROUNDING CONTEXT" not in client.last_system_prompt


def test_generation_grounding_override_on_empty_recs() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.RECOMMEND,
        grounding_assessments=[
            GroundingAssessment(
                name="Python Test",
                description="Python assessment",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://python",
            )
        ],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND),
    )
    client = MockGenerationClient([
        {"content": '{"reply": "No matches found", "recommended_names": []}'}
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(pkg)

    assert "most relevant assessments" in result.reply
    assert result.recommended_names == ["Python Test"]


def test_generation_grounding_override_on_not_enough_info() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.RECOMMEND,
        grounding_assessments=[
            GroundingAssessment(
                name="Java Test",
                description="Java assessment",
                duration="45 min",
                job_levels=["Senior"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://java",
            )
        ],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND),
    )
    client = MockGenerationClient([
        {
            "content": '{"reply": "I do not have enough information to recommend a specific assessment.", "recommended_names": []}'
        }
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(pkg)

    assert "most relevant assessments" in result.reply
    assert result.recommended_names == ["Java Test"]


def test_generation_grounding_override_does_not_fire_on_valid_recs() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.RECOMMEND,
        grounding_assessments=[
            GroundingAssessment(
                name="Python Test",
                description="Python assessment",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://python",
            ),
            GroundingAssessment(
                name="Java Test",
                description="Java assessment",
                duration="45 min",
                job_levels=["Senior"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://java",
            ),
        ],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.RECOMMEND),
    )
    client = MockGenerationClient([
        {
            "content": '{"reply": "Here are options", "recommended_names": ["Python Test"], "end_of_conversation": false}'
        }
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(pkg)

    assert result.reply == "Here are options"
    assert result.recommended_names == ["Python Test"]


def test_generation_grounding_override_on_compare_route() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.COMPARE,
        grounding_assessments=[
            GroundingAssessment(
                name="OPQ32r",
                description="Personality questionnaire",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Personality"],
                link="http://opq",
            ),
            GroundingAssessment(
                name="Verify Interactive",
                description="Interactive reasoning",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Cognitive"],
                link="http://verify",
            ),
        ],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.COMPARE),
    )
    client = MockGenerationClient([
        {
            "content": '{"reply": "Not enough information to compare", "recommended_names": [], "end_of_conversation": false}'
        }
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(pkg)

    assert result.recommended_names == ["OPQ32r", "Verify Interactive"]


def test_generation_grounding_override_on_refine_route() -> None:
    pkg = PromptPackage(
        system_prompt="Base",
        user_prompt="User",
        route=RouteType.REFINE,
        grounding_assessments=[
            GroundingAssessment(
                name="Python Test",
                description="Python assessment",
                duration="30 min",
                job_levels=["Mid"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge"],
                link="http://python",
            )
        ],
        metadata=PromptMetadata(prompt_version="1.0", route=RouteType.REFINE),
    )
    client = MockGenerationClient([
        {"content": '{"reply": "No suggestions", "recommended_names": []}'}
    ])
    generator = ResponseGenerator(client=client)

    result = generator.generate(pkg)

    assert result.recommended_names == ["Python Test"]
    assert "most relevant assessments" in result.reply
