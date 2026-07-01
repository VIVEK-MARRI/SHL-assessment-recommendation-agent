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


def test_generation_markdown_json(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": '```json\n{"reply": "Hello", "recommended_names": []}\n```'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    assert result.reply == "Hello"


def test_generation_retry_success_on_malformed_json(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": 'Oops this is not JSON'},
        {"content": '{"reply": "Now it is JSON", "recommended_names": []}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
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


def test_generation_retry_success_on_rate_limit(package: PromptPackage) -> None:
    client = MockGenerationClient([
        RateLimitError("429"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    assert result.reply == "Success"
    assert client.call_count == 2


def test_generation_timeout_retry(package: PromptPackage) -> None:
    client = MockGenerationClient([
        GenerationTimeoutError("timeout"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    assert result.reply == "Success"
    assert client.call_count == 2


def test_generation_provider_error_503_retry(package: PromptPackage) -> None:
    client = MockGenerationClient([
        ProviderError("LLM request failed: 503 Service Unavailable"),
        {"content": '{"reply": "Success"}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
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


def test_generation_empty_recommendations(package: PromptPackage) -> None:
    client = MockGenerationClient([
        {"content": '{"reply": "No matches", "recommended_names": [], "end_of_conversation": false}'}
    ])
    generator = ResponseGenerator(client=client)
    
    result = generator.generate(package)
    assert result.recommended_names == []


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
