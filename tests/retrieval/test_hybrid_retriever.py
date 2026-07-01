"""Unit tests for retrieval.hybrid_retriever."""

from __future__ import annotations

import pytest

from retrieval.confidence_gate import ConfidenceGate
from retrieval.hybrid_retriever import HybridRetriever, HybridRetrieverError
from retrieval.retrieval_models import (
    BM25RetrieverHealth,
    EmbeddingRetrieverHealth,
    RetrievedAssessment,
)


class FakeEmbeddingRetriever:
    def __init__(
        self,
        results: list[RetrievedAssessment] | None = None,
        *,
        catalog_sha: str = "sha",
        fail_initialize: bool = False,
    ) -> None:
        self.results = results or []
        self.catalog_sha = catalog_sha
        self.fail_initialize = fail_initialize
        self.initialized = False
        self.calls = 0

    def initialize(self) -> None:
        if self.fail_initialize:
            from retrieval.embedding_retriever import EmbeddingRetrieverError

            raise EmbeddingRetrieverError("boom")
        self.initialized = True

    def search(self, query: str, top_k: int = 20, minimum_score: float = 0.0):
        self.calls += 1
        return self.results[:top_k]

    def health(self) -> EmbeddingRetrieverHealth:
        return EmbeddingRetrieverHealth(
            index_loaded=self.initialized,
            model_loaded=self.initialized,
            metadata_loaded=self.initialized,
            model_name="fake-model",
            catalog_sha=self.catalog_sha,
            average_query_latency_ms=2.0 if self.calls else None,
        )


class FakeBM25Retriever:
    def __init__(
        self,
        results: list[RetrievedAssessment] | None = None,
        *,
        catalog_sha: str = "sha",
        fail_initialize: bool = False,
    ) -> None:
        self.results = results or []
        self.catalog_sha = catalog_sha
        self.fail_initialize = fail_initialize
        self.initialized = False
        self.calls = 0

    def initialize(self) -> None:
        if self.fail_initialize:
            from retrieval.bm25_retriever import BM25RetrieverError

            raise BM25RetrieverError("boom")
        self.initialized = True

    def search(self, query: str, top_k: int = 20, minimum_score: float = 0.0):
        self.calls += 1
        return self.results[:top_k]

    def health(self) -> BM25RetrieverHealth:
        return BM25RetrieverHealth(
            bm25_loaded=self.initialized,
            corpus_loaded=self.initialized,
            document_count=len(self.results),
            tokenizer_version="1.0",
            catalog_sha256=self.catalog_sha,
            average_query_latency_ms=1.0 if self.calls else None,
        )


def _result(entity_id: str, source: str, rank: int) -> RetrievedAssessment:
    return RetrievedAssessment(
        retrieval_source=source,
        entity_id=entity_id,
        name=f"Assessment {entity_id}",
        url=f"https://www.shl.com/{entity_id}",
        score=1.0,
        rank=rank,
        embedding_rank=rank if source == "embedding" else None,
        bm25_rank=rank if source == "bm25" else None,
    )


def _hybrid() -> HybridRetriever:
    return HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever(
            [_result("a", "embedding", 1), _result("b", "embedding", 2)]
        ),
        bm25_retriever=FakeBM25Retriever(
            [_result("a", "bm25", 1), _result("c", "bm25", 2)]
        ),
    )


def test_initialize_and_health() -> None:
    retriever = _hybrid()
    retriever.initialize()

    health = retriever.health()
    assert health.embedding_ready is True
    assert health.bm25_ready is True
    assert health.rrf_ready is True
    assert health.catalog_sha256 == "sha"
    assert health.embedding_model == "fake-model"
    assert health.tokenizer_version == "1.0"


def test_search_returns_confident_hybrid_results() -> None:
    retriever = _hybrid()
    retriever.initialize()
    result = retriever.search("java developer", top_k=5)

    assert result.confidence == "HIGH"
    assert result.results[0].entity_id == "a"
    assert result.results[0].retrieval_source == "hybrid"
    assert result.results[0].rrf_score is not None
    assert result.results[0].embedding_rank == 1
    assert result.results[0].bm25_rank == 1
    assert len({item.entity_id for item in result.results}) == len(result.results)


def test_top_k_is_applied_after_fusion() -> None:
    retriever = _hybrid()
    retriever.initialize()

    result = retriever.search("java developer", top_k=1)

    assert len(result.results) == 1


def test_latency_recorded() -> None:
    retriever = _hybrid()
    retriever.initialize()
    retriever.search("java developer")

    assert retriever.health().average_latency_ms is not None


def test_deterministic_output() -> None:
    retriever = _hybrid()
    retriever.initialize()

    first = retriever.search("java developer")
    second = retriever.search("java developer")

    assert first.model_dump() == second.model_dump()


def test_uninitialized_search_raises() -> None:
    with pytest.raises(HybridRetrieverError, match="not initialized"):
        _hybrid().search("java developer")


def test_embedding_retriever_unavailable_raises() -> None:
    retriever = HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever(fail_initialize=True),
        bm25_retriever=FakeBM25Retriever(),
    )

    with pytest.raises(HybridRetrieverError, match="Embedding retriever unavailable"):
        retriever.initialize()


def test_bm25_retriever_unavailable_raises() -> None:
    retriever = HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever(),
        bm25_retriever=FakeBM25Retriever(fail_initialize=True),
    )

    with pytest.raises(HybridRetrieverError, match="BM25 retriever unavailable"):
        retriever.initialize()


def test_catalog_mismatch_raises() -> None:
    retriever = HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever(catalog_sha="embedding"),
        bm25_retriever=FakeBM25Retriever(catalog_sha="bm25"),
    )

    with pytest.raises(HybridRetrieverError, match="Catalog SHA mismatch"):
        retriever.initialize()


def test_empty_retrieval_raises() -> None:
    retriever = HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever([]),
        bm25_retriever=FakeBM25Retriever([]),
    )
    retriever.initialize()

    with pytest.raises(HybridRetrieverError, match="Empty retrieval"):
        retriever.search("unknown")


def test_confidence_low_for_no_overlap() -> None:
    retriever = HybridRetriever(
        embedding_retriever=FakeEmbeddingRetriever([_result("a", "embedding", 1)]),
        bm25_retriever=FakeBM25Retriever([_result("b", "bm25", 1)]),
        confidence_gate=ConfidenceGate(),
    )
    retriever.initialize()

    result = retriever.search("split evidence")

    assert result.confidence == "LOW"

