"""Production lexical retriever backed by the persistent BM25 index."""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from rank_bm25 import BM25Okapi

from retrieval.bm25_loader import BM25LoadError, LoadedBM25Index, load_bm25_index
from retrieval.bm25_models import BM25Config, BM25DocumentRecord
from retrieval.bm25_search import BM25SearchError, search_bm25 as search_loaded_bm25
from retrieval.bm25_tokenizer import tokenize
from retrieval.constants import BM25_CONFIG_PATH, BM25_CORPUS_PATH, BM25_INDEX_PATH
from retrieval.retrieval_models import BM25RetrieverHealth, RetrievedAssessment

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


class BM25RetrieverError(Exception):
    """Raised when the lexical BM25 retriever cannot serve a query."""


class BM25Retriever:
    """Lexical retriever using the persisted Module 08 BM25 index."""

    def __init__(
        self,
        index_path: Path = BM25_INDEX_PATH,
        corpus_path: Path = BM25_CORPUS_PATH,
        config_path: Path = BM25_CONFIG_PATH,
        *,
        catalog_path: Path | None = None,
        loader: Callable[..., LoadedBM25Index] = load_bm25_index,
    ) -> None:
        """Create a BM25 retriever with injectable persistence dependencies."""
        self._index_path = index_path
        self._corpus_path = corpus_path
        self._config_path = config_path
        self._catalog_path = catalog_path
        self._loader = loader
        self._index: BM25Okapi | None = None
        self._documents: list[BM25DocumentRecord] = []
        self._config: BM25Config | None = None
        self._query_latencies_ms: list[float] = []

    def initialize(self) -> None:
        """Load the persisted BM25 index, corpus, and config."""
        started_at = perf_counter()
        try:
            loaded = self._loader(
                self._index_path,
                self._corpus_path,
                self._config_path,
                catalog_path=self._catalog_path,
            )
        except BM25LoadError as exc:
            raise BM25RetrieverError(f"BM25 retriever initialization failed: {exc}") from exc
        except Exception as exc:
            raise BM25RetrieverError(f"BM25 retriever loading failure: {exc}") from exc

        if len(loaded.index.doc_len) != loaded.config.document_count:
            raise BM25RetrieverError(
                f"Configuration mismatch: BM25 index has {len(loaded.index.doc_len)} "
                f"documents but config declares {loaded.config.document_count}."
            )

        self._index = loaded.index
        self._documents = loaded.documents
        self._config = loaded.config
        logger.info(
            "Retriever initialized: documents=%d tokenizer=%s elapsed_ms=%.2f",
            self._config.document_count,
            self._config.tokenizer_version,
            (perf_counter() - started_at) * 1000,
        )

    def search(
        self,
        query: str,
        top_k: int = 20,
        minimum_score: float = 0.0,
    ) -> list[RetrievedAssessment]:
        """Return ranked lexical assessment candidates for a user query."""
        started_at = perf_counter()
        self._ensure_initialized()
        normalized_query = self._normalize_query(query)
        logger.info("Query normalized: chars=%d", len(normalized_query))

        query_tokens = tokenize(normalized_query)
        if not query_tokens:
            raise BM25RetrieverError("query must contain at least one token")
        logger.info("Tokenized query: tokens=%d", len(query_tokens))

        try:
            results = search_loaded_bm25(
                self._index,
                self._documents,
                query_tokens,
                top_k=top_k,
                minimum_score=minimum_score,
            )
        except BM25SearchError as exc:
            raise BM25RetrieverError(str(exc)) from exc

        elapsed_ms = (perf_counter() - started_at) * 1000
        self._query_latencies_ms.append(elapsed_ms)
        logger.info(
            "Search completed: returned=%d elapsed_ms=%.2f",
            len(results),
            elapsed_ms,
        )
        return results

    def health(self) -> BM25RetrieverHealth:
        """Return current retriever health and loaded BM25 metadata."""
        average_latency = (
            sum(self._query_latencies_ms) / len(self._query_latencies_ms)
            if self._query_latencies_ms
            else None
        )
        return BM25RetrieverHealth(
            bm25_loaded=self._index is not None,
            corpus_loaded=bool(self._documents),
            document_count=self._config.document_count if self._config else 0,
            tokenizer_version=self._config.tokenizer_version if self._config else None,
            catalog_sha256=self._config.catalog_sha256 if self._config else None,
            average_query_latency_ms=average_latency,
        )

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Normalize a query with NFKC, whitespace collapse, and trimming."""
        if not isinstance(query, str):
            raise BM25RetrieverError("query must be a string")
        normalized = unicodedata.normalize("NFKC", query)
        normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
        if not normalized:
            raise BM25RetrieverError("query must not be empty")
        return normalized

    def _ensure_initialized(self) -> None:
        if self._index is None or self._config is None:
            raise BM25RetrieverError("BM25 retriever is not initialized")


def search_bm25(
    query: str,
    top_k: int = 20,
    minimum_score: float = 0.0,
) -> list[RetrievedAssessment]:
    """Convenience API for one-off lexical searches with default artifacts."""
    retriever = BM25Retriever()
    retriever.initialize()
    return retriever.search(query, top_k=top_k, minimum_score=minimum_score)
