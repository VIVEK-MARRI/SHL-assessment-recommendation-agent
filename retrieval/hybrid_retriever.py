"""Hybrid retrieval engine combining semantic and lexical retrievers."""

from __future__ import annotations

import logging
from time import perf_counter

from retrieval.bm25_retriever import BM25Retriever, BM25RetrieverError
from retrieval.confidence_gate import ConfidenceGate, ConfidenceGateError
from retrieval.embedding_retriever import EmbeddingRetriever, EmbeddingRetrieverError
from retrieval.reciprocal_rank_fusion import RRFError, reciprocal_rank_fusion
from retrieval.retrieval_models import HybridRetrievalResult, HybridRetrieverHealth

logger = logging.getLogger(__name__)


class HybridRetrieverError(Exception):
    """Raised when the hybrid retrieval engine cannot serve a query."""


class HybridRetriever:
    """Orchestrates embedding and BM25 retrievers with RRF fusion."""

    def __init__(
        self,
        embedding_retriever: EmbeddingRetriever | None = None,
        bm25_retriever: BM25Retriever | None = None,
        confidence_gate: ConfidenceGate | None = None,
    ) -> None:
        """Create a hybrid retriever with injectable retriever dependencies."""
        self._embedding_retriever = embedding_retriever or EmbeddingRetriever()
        self._bm25_retriever = bm25_retriever or BM25Retriever()
        self._confidence_gate = confidence_gate or ConfidenceGate()
        self._initialized = False
        self._latencies_ms: list[float] = []

    def initialize(self) -> None:
        """Initialize both underlying retrievers and verify catalog alignment."""
        try:
            self._embedding_retriever.initialize()
        except EmbeddingRetrieverError as exc:
            raise HybridRetrieverError(f"Embedding retriever unavailable: {exc}") from exc
        try:
            self._bm25_retriever.initialize()
        except BM25RetrieverError as exc:
            raise HybridRetrieverError(f"BM25 retriever unavailable: {exc}") from exc

        self._validate_catalog_alignment()
        self._initialized = True
        logger.info("Hybrid retriever initialized")

    def search(
        self,
        query: str,
        top_k: int = 20,
        minimum_score: float = 0.0,
    ) -> HybridRetrievalResult:
        """Return fused hybrid retrieval results with confidence metadata."""
        if top_k < 1:
            raise HybridRetrieverError("top_k must be greater than or equal to 1")
        self._ensure_initialized()
        started_at = perf_counter()

        try:
            embedding_results = self._embedding_retriever.search(
                query,
                top_k=top_k,
                minimum_score=minimum_score,
            )
            logger.info("Embedding retrieval completed: returned=%d", len(embedding_results))
            bm25_results = self._bm25_retriever.search(
                query,
                top_k=top_k,
                minimum_score=minimum_score,
            )
            logger.info("BM25 retrieval completed: returned=%d", len(bm25_results))
        except (EmbeddingRetrieverError, BM25RetrieverError) as exc:
            raise HybridRetrieverError(f"Underlying retriever failure: {exc}") from exc

        if not embedding_results and not bm25_results:
            raise HybridRetrieverError("Empty retrieval from both retrievers")

        try:
            fused_results = reciprocal_rank_fusion(
                embedding_results,
                bm25_results,
                top_k=top_k,
            )
            logger.info("Deduplication completed: results=%d", len(fused_results))
            result = self._confidence_gate.evaluate(
                fused_results,
                embedding_results,
                bm25_results,
            )
        except (RRFError, ConfidenceGateError) as exc:
            raise HybridRetrieverError(f"Hybrid retrieval failure: {exc}") from exc

        elapsed_ms = (perf_counter() - started_at) * 1000
        self._latencies_ms.append(elapsed_ms)
        logger.info(
            "Results returned: count=%d confidence=%s elapsed_ms=%.2f",
            len(result.results),
            result.confidence,
            elapsed_ms,
        )
        return result

    def health(self) -> HybridRetrieverHealth:
        """Return current hybrid retriever health."""
        embedding_health = self._embedding_retriever.health()
        bm25_health = self._bm25_retriever.health()
        average_latency = (
            sum(self._latencies_ms) / len(self._latencies_ms)
            if self._latencies_ms
            else None
        )
        catalog_sha = embedding_health.catalog_sha or bm25_health.catalog_sha256
        return HybridRetrieverHealth(
            embedding_ready=embedding_health.index_loaded and embedding_health.model_loaded,
            bm25_ready=bm25_health.bm25_loaded and bm25_health.corpus_loaded,
            rrf_ready=self._initialized,
            catalog_sha256=catalog_sha,
            embedding_model=embedding_health.model_name,
            tokenizer_version=bm25_health.tokenizer_version,
            embedding_latency_ms=embedding_health.average_query_latency_ms,
            bm25_latency_ms=bm25_health.average_query_latency_ms,
            average_latency_ms=average_latency,
        )

    def _validate_catalog_alignment(self) -> None:
        embedding_sha = self._embedding_retriever.health().catalog_sha
        bm25_sha = self._bm25_retriever.health().catalog_sha256
        if embedding_sha and bm25_sha and embedding_sha != bm25_sha:
            raise HybridRetrieverError(
                f"Catalog SHA mismatch: embedding={embedding_sha} bm25={bm25_sha}"
            )

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise HybridRetrieverError("Hybrid retriever is not initialized")
