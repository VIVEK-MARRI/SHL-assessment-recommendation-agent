"""Tests for the health and root API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from retrieval.retrieval_models import HybridRetrieverHealth


def _mock_container(embedding_ready: bool = True, bm25_ready: bool = True, provider: str = "groq"):
    health = HybridRetrieverHealth(
        embedding_ready=embedding_ready,
        bm25_ready=bm25_ready,
        rrf_ready=True,
    )
    retriever_mock = MagicMock()
    retriever_mock.health.return_value = health

    container = MagicMock()
    container.hybrid_retriever = retriever_mock
    container.llm_provider = provider
    return container


@pytest.fixture
def client():
    app = create_app()
    # Pre-inject the container so lifespan does not try to build it from env
    app.state.container = _mock_container()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "SHL Assessment Recommendation Agent"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_endpoint_all_ready(client: TestClient) -> None:
    client.app.state.container = _mock_container(embedding_ready=True, bm25_ready=True)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["catalog_loaded"] is True
    assert data["embedding_index_loaded"] is True
    assert data["bm25_index_loaded"] is True
    assert data["llm_provider"] == "groq"
    assert data["version"] == "1.0.0"


def test_health_endpoint_partial_ready(client: TestClient) -> None:
    client.app.state.container = _mock_container(embedding_ready=False, bm25_ready=True)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["embedding_index_loaded"] is False
    assert data["bm25_index_loaded"] is True
