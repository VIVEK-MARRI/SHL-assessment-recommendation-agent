import pytest
import httpx

from agent.llm_client import LLMClientConfig
from agent.generation_client import (
    GenerationClient,
    GenerationTimeoutError,
    JSONGenerationError,
    ProviderError,
    RateLimitError,
)

class MockResponse:
    def __init__(self, status_code: int, json_data: dict, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> dict:
        if self._json_data is None:
            raise ValueError("Invalid JSON")
        return self._json_data


class MockHttpClient:
    def __init__(self, response: MockResponse | Exception):
        self.response = response
        self.post_called = 0

    def post(self, *args, **kwargs) -> MockResponse:
        self.post_called += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def config() -> LLMClientConfig:
    return LLMClientConfig(
        provider="groq",
        api_key="test-key",
        model="test-model",
    )


def test_generation_client_success(config: LLMClientConfig) -> None:
    mock_response = MockResponse(
        status_code=200,
        json_data={
            "choices": [
                {
                    "message": {"content": '{"reply": "Hello"}'},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
    )
    http_client = MockHttpClient(mock_response) # type: ignore
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    result = client.generate("system", "user")
    
    assert result["content"] == '{"reply": "Hello"}'
    assert result["provider"] == "groq"
    assert result["model"] == "test-model"
    assert result["tokens_prompt"] == 10
    assert result["tokens_completion"] == 5
    assert result["tokens_total"] == 15
    assert result["finish_reason"] == "stop"
    assert result["latency_ms"] >= 0


def test_generation_client_timeout(config: LLMClientConfig) -> None:
    http_client = MockHttpClient(httpx.TimeoutException("timeout"))
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    with pytest.raises(GenerationTimeoutError):
        client.generate("system", "user")


def test_generation_client_rate_limit(config: LLMClientConfig) -> None:
    http_client = MockHttpClient(MockResponse(429, {}, "rate limited")) # type: ignore
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    with pytest.raises(RateLimitError):
        client.generate("system", "user")


def test_generation_client_503(config: LLMClientConfig) -> None:
    http_client = MockHttpClient(MockResponse(503, {}, "service unavailable")) # type: ignore
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    with pytest.raises(ProviderError) as excinfo:
        client.generate("system", "user")
    assert "503" in str(excinfo.value)


def test_generation_client_invalid_json(config: LLMClientConfig) -> None:
    # Simulates provider returning HTML instead of JSON wrapper
    http_client = MockHttpClient(MockResponse(200, None, "<html></html>")) # type: ignore
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    with pytest.raises(ProviderError) as excinfo:
        client.generate("system", "user")
    assert "valid JSON wrapper" in str(excinfo.value)


def test_generation_client_empty_content(config: LLMClientConfig) -> None:
    mock_response = MockResponse(
        status_code=200,
        json_data={
            "choices": [{"message": {"content": ""}}]
        }
    )
    http_client = MockHttpClient(mock_response) # type: ignore
    client = GenerationClient(config=config, http_client=http_client) # type: ignore
    
    with pytest.raises(JSONGenerationError) as excinfo:
        client.generate("system", "user")
    assert "empty" in str(excinfo.value)
