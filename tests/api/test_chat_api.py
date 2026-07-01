"""Tests for the /chat API endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from agent.generation_client import ProviderError, RateLimitError
from agent.response_models import ChatResponse, Recommendation
from agent.validator import InvalidGenerationResult
from app.main import create_app


def _build_client(chat_response=None, side_effect=None):
    """Return a TestClient with a fully mocked container, bypassing lifespan."""
    app = create_app()

    container = MagicMock()
    if side_effect:
        container.chat_service.chat.side_effect = side_effect
    else:
        container.chat_service.chat.return_value = chat_response or ChatResponse(
            reply="Here is a recommendation.",
            recommendations=[
                Recommendation(
                    name="Python Advanced",
                    url="http://shl.com/python",
                    test_type=["Knowledge & Skills"],
                )
            ],
        )

    # Pre-inject to avoid lifespan calling AppContainer()
    app.state.container = container
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def success_client():
    return _build_client()


@pytest.fixture
def rate_limit_client():
    return _build_client(side_effect=RateLimitError("429"))


@pytest.fixture
def provider_error_client():
    return _build_client(side_effect=ProviderError("Provider error"))


@pytest.fixture
def validation_error_client():
    return _build_client(side_effect=InvalidGenerationResult("empty reply"))


@pytest.fixture
def internal_error_client():
    return _build_client(side_effect=RuntimeError("Unexpected"))


def test_chat_success(success_client) -> None:
    response = success_client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Python test for senior engineers"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Here is a recommendation."
    assert data["recommendations"] is not None
    assert data["recommendations"][0]["name"] == "Python Advanced"
    assert data["recommendations"][0]["url"] == "http://shl.com/python"
    assert data["recommendations"][0]["test_type"] == ["Knowledge & Skills"]


def test_chat_clarify_null_recommendations() -> None:
    client = _build_client(
        chat_response=ChatResponse(
            reply="What seniority level?",
            recommendations=None,
        )
    )
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "I need a test."}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] is None


def test_chat_empty_messages(success_client) -> None:
    response = success_client.post(
        "/chat",
        json={"messages": []},
    )
    assert response.status_code in (400, 422)


def test_chat_malformed_json(success_client) -> None:
    response = success_client.post(
        "/chat",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_chat_rate_limit(rate_limit_client) -> None:
    response = rate_limit_client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 429


def test_chat_provider_unavailable(provider_error_client) -> None:
    response = provider_error_client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 503


def test_chat_validation_failure(validation_error_client) -> None:
    response = validation_error_client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 500


def test_chat_internal_error(internal_error_client) -> None:
    response = internal_error_client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 500
