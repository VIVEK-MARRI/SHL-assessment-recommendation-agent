"""Low-level FAISS search for semantic assessment retrieval."""

from __future__ import annotations

import logging
from time import perf_counter

import faiss
import numpy as np

from retrieval.models import AssessmentMetadataRecord
from retrieval.retrieval_models import RetrievedAssessment

logger = logging.getLogger(__name__)


class EmbeddingSearchError(Exception):
    """Raised when FAISS semantic search cannot be completed."""


def search_embeddings(
    index: faiss.Index,
    metadata: list[AssessmentMetadataRecord],
    query_vector: np.ndarray,
    top_k: int = 20,
    minimum_score: float = 0.0,
) -> list[RetrievedAssessment]:
    """Search a loaded FAISS embedding index and resolve metadata.

    Args:
        index: Loaded FAISS IndexFlatIP containing normalized assessment vectors.
        metadata: Metadata records ordered by FAISS vector offset.
        query_vector: One normalized query vector with shape ``(dim,)`` or ``(1, dim)``.
        top_k: Maximum number of candidates to retrieve before score filtering.
        minimum_score: Minimum cosine similarity score to include.

    Returns:
        Ranked retrieval candidates sorted by descending similarity.

    Raises:
        EmbeddingSearchError: If search parameters, dimensions, metadata, or FAISS
            execution are invalid.
    """
    started_at = perf_counter()
    if top_k < 1:
        raise EmbeddingSearchError("top_k must be greater than or equal to 1")
    if not np.isfinite(minimum_score):
        raise EmbeddingSearchError("minimum_score must be finite")
    if index.ntotal != len(metadata):
        raise EmbeddingSearchError(
            f"Metadata mismatch: FAISS index has {index.ntotal} vectors but "
            f"metadata has {len(metadata)} records."
        )

    vector = np.asarray(query_vector, dtype=np.float32)
    if vector.ndim == 1:
        vector = vector.reshape(1, -1)
    if vector.ndim != 2 or vector.shape[0] != 1:
        raise EmbeddingSearchError("query_vector must contain exactly one embedding")
    if vector.shape[1] != index.d:
        raise EmbeddingSearchError(
            f"Dimension mismatch: query vector has dimension {vector.shape[1]} "
            f"but FAISS index dimension is {index.d}."
        )

    k = min(top_k, int(index.ntotal))
    try:
        scores, offsets = index.search(vector, k)
    except Exception as exc:
        raise EmbeddingSearchError(f"FAISS search failed: {exc}") from exc

    logger.info(
        "FAISS search completed: top_k=%d elapsed_ms=%.2f",
        k,
        (perf_counter() - started_at) * 1000,
    )

    raw_matches: list[tuple[float, int]] = []
    for score, offset in zip(scores[0].tolist(), offsets[0].tolist()):
        if offset < 0:
            continue
        if offset >= len(metadata):
            raise EmbeddingSearchError(f"FAISS returned metadata offset out of range: {offset}")
        score_value = float(score)
        if score_value >= minimum_score:
            raw_matches.append((score_value, int(offset)))

    raw_matches.sort(key=lambda item: (-item[0], item[1]))
    results: list[RetrievedAssessment] = []
    seen_entity_ids: set[str] = set()
    for embedding_rank, (score, offset) in enumerate(raw_matches, start=1):
        record = metadata[offset]
        if record.entity_id in seen_entity_ids:
            continue
        seen_entity_ids.add(record.entity_id)
        results.append(
            RetrievedAssessment(
                entity_id=record.entity_id,
                name=record.name,
                description=record.description,
                url=record.url,
                test_type=record.test_type,
                score=score,
                rank=len(results) + 1,
                embedding_rank=embedding_rank,
                job_levels=list(record.job_levels),
                languages=list(record.languages),
                duration=record.duration,
                duration_minutes=record.duration_minutes,
                remote=record.remote,
                adaptive=record.adaptive,
                keys=list(record.keys),
            )
        )

    logger.info(
        "Results returned: count=%d elapsed_ms=%.2f",
        len(results),
        (perf_counter() - started_at) * 1000,
    )
    return results
