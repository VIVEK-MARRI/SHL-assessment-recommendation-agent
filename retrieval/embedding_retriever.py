"""Production semantic retriever backed by the persistent FAISS embedding index."""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from retrieval.constants import CONFIG_PATH, FAISS_INDEX_PATH, METADATA_PATH
from retrieval.embedding_generator import EmbeddingModelError, get_model
from retrieval.embedding_search import (
    EmbeddingSearchError,
    search_embeddings as search_loaded_embeddings,
)
from retrieval.index_loader import EmbeddingIndexLoadError, LoadedIndex, load_embedding_index
from retrieval.models import AssessmentMetadataRecord, EmbeddingConfig
from retrieval.retrieval_models import EmbeddingRetrieverHealth, RetrievedAssessment

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


class EmbeddingRetrieverError(Exception):
    """Raised when the semantic embedding retriever cannot serve a query."""


class EmbeddingRetriever:
    """Semantic retriever using the persisted Module 07 FAISS embedding index."""

    def __init__(
        self,
        index_path: Path = FAISS_INDEX_PATH,
        metadata_path: Path = METADATA_PATH,
        config_path: Path = CONFIG_PATH,
        *,
        catalog_path: Path | None = None,
        model_provider: Callable[[], SentenceTransformer] = get_model,
    ) -> None:
        """Create an embedding retriever with injectable persistence/model dependencies.

        Args:
            index_path: Path to ``embedding.index``.
            metadata_path: Path to ``embedding_metadata.json``.
            config_path: Path to ``embedding_config.json``.
            catalog_path: Optional catalog path for index SHA staleness checks.
            model_provider: Callable returning the singleton embedding model.
        """
        self._index_path = index_path
        self._metadata_path = metadata_path
        self._config_path = config_path
        self._catalog_path = catalog_path
        self._model_provider = model_provider
        self._index: faiss.Index | None = None
        self._metadata: list[AssessmentMetadataRecord] = []
        self._config: EmbeddingConfig | None = None
        self._model: SentenceTransformer | None = None
        self._query_latencies_ms: list[float] = []

    def initialize(self) -> None:
        """Load the persisted FAISS index, metadata, config, and singleton model.

        Raises:
            EmbeddingRetrieverError: If the index artifacts or embedding model cannot
                be loaded, or if their dimensions/configuration are incompatible.
        """
        started_at = perf_counter()
        try:
            loaded: LoadedIndex = load_embedding_index(
                self._index_path,
                self._metadata_path,
                self._config_path,
                catalog_path=self._catalog_path,
            )
            self._model = self._model_provider()
        except (EmbeddingIndexLoadError, EmbeddingModelError) as exc:
            raise EmbeddingRetrieverError(
                f"Embedding retriever initialization failed: {exc}"
            ) from exc
        except Exception as exc:
            raise EmbeddingRetrieverError(f"Embedding model loading failure: {exc}") from exc

        self._index = loaded.index
        self._metadata = loaded.metadata
        self._config = loaded.config

        if self._index.d != self._config.embedding_dim:
            raise EmbeddingRetrieverError(
                f"Configuration mismatch: index dimension {self._index.d} "
                f"does not match config embedding_dim {self._config.embedding_dim}."
            )

        logger.info(
            "Retriever initialized: assessments=%d dim=%d elapsed_ms=%.2f",
            self._config.num_assessments,
            self._config.embedding_dim,
            (perf_counter() - started_at) * 1000,
        )

    def search(
        self,
        query: str,
        top_k: int = 20,
        minimum_score: float = 0.0,
    ) -> list[RetrievedAssessment]:
        """Return ranked semantic assessment candidates for a user query.

        Args:
            query: User search text.
            top_k: Maximum number of FAISS candidates to retrieve.
            minimum_score: Minimum cosine similarity score to include.

        Returns:
            Ranked assessment candidates.

        Raises:
            EmbeddingRetrieverError: If the retriever is uninitialized, the query is
                invalid, embedding generation fails, or FAISS search fails.
        """
        started_at = perf_counter()
        self._ensure_initialized()
        normalized_query = self._normalize_query(query)
        logger.info("Query normalized: chars=%d", len(normalized_query))

        query_vector = self._generate_query_embedding(normalized_query)
        logger.info("Embedding generated: dimension=%d", query_vector.shape[0])

        try:
            results = search_loaded_embeddings(
                self._index,
                self._metadata,
                query_vector,
                top_k=top_k,
                minimum_score=minimum_score,
            )
        except EmbeddingSearchError as exc:
            raise EmbeddingRetrieverError(str(exc)) from exc

        elapsed_ms = (perf_counter() - started_at) * 1000
        self._query_latencies_ms.append(elapsed_ms)
        logger.info(
            "Search completed: returned=%d elapsed_ms=%.2f",
            len(results),
            elapsed_ms,
        )
        return results

    def health(self) -> EmbeddingRetrieverHealth:
        """Return current retriever health and loaded index metadata."""
        average_latency = (
            sum(self._query_latencies_ms) / len(self._query_latencies_ms)
            if self._query_latencies_ms
            else None
        )
        return EmbeddingRetrieverHealth(
            index_loaded=self._index is not None,
            model_loaded=self._model is not None,
            metadata_loaded=bool(self._metadata),
            model_name=self._config.embedding_model if self._config else None,
            embedding_dimension=self._config.embedding_dim if self._config else None,
            number_of_indexed_assessments=self._config.num_assessments if self._config else 0,
            catalog_sha=self._config.catalog_sha256 if self._config else None,
            average_query_latency_ms=average_latency,
        )

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Normalize a query with NFKC, whitespace collapse, and trimming."""
        if not isinstance(query, str):
            raise EmbeddingRetrieverError("query must be a string")
        normalized = unicodedata.normalize("NFKC", query)
        normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
        if not normalized:
            raise EmbeddingRetrieverError("query must not be empty")
        return normalized

    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate exactly one L2-normalized query embedding vector."""
        if self._model is None or self._config is None:
            raise EmbeddingRetrieverError("Embedding retriever is not initialized")
        try:
            encoded = self._model.encode(
                [query],
                batch_size=1,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise EmbeddingRetrieverError(f"Query embedding generation failed: {exc}") from exc

        vector = np.asarray(encoded, dtype=np.float32)
        if vector.ndim != 2 or vector.shape[0] != 1:
            raise EmbeddingRetrieverError(
                "Query embedding generation did not return exactly one vector"
            )
        if vector.shape[1] != self._config.embedding_dim:
            raise EmbeddingRetrieverError(
                f"Dimension mismatch: query embedding dimension {vector.shape[1]} "
                f"does not match index dimension {self._config.embedding_dim}."
            )

        norm = np.linalg.norm(vector, axis=1, keepdims=True)
        if not np.all(np.isfinite(norm)) or float(norm[0][0]) == 0.0:
            raise EmbeddingRetrieverError("Query embedding is invalid and cannot be normalized")
        vector = vector / norm
        return vector[0].astype(np.float32)

    def _ensure_initialized(self) -> None:
        """Raise if the persistent index or model has not been initialized."""
        if self._index is None or self._config is None or self._model is None:
            raise EmbeddingRetrieverError("Embedding retriever is not initialized")


def search_embeddings(
    query: str,
    top_k: int = 20,
    minimum_score: float = 0.0,
) -> list[RetrievedAssessment]:
    """Convenience API for one-off semantic searches with default artifacts.

    Args:
        query: User search text.
        top_k: Maximum number of candidates to retrieve.
        minimum_score: Minimum cosine similarity score to include.

    Returns:
        Ranked assessment candidates.
    """
    retriever = EmbeddingRetriever()
    retriever.initialize()
    return retriever.search(query, top_k=top_k, minimum_score=minimum_score)
