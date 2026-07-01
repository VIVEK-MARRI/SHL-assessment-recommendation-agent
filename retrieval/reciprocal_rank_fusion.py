"""Reciprocal Rank Fusion for hybrid assessment retrieval."""

from __future__ import annotations

import logging
import math
from time import perf_counter

from retrieval.retrieval_models import RetrievedAssessment

logger = logging.getLogger(__name__)

RRF_K: int = 60


class RRFError(Exception):
    """Raised when reciprocal rank fusion cannot be completed."""


def reciprocal_rank_fusion(
    embedding_results: list[RetrievedAssessment],
    bm25_results: list[RetrievedAssessment],
    top_k: int = 20,
    k: int = RRF_K,
) -> list[RetrievedAssessment]:
    """Fuse semantic and lexical ranked results using standard RRF.

    Args:
        embedding_results: Results from ``EmbeddingRetriever.search()``.
        bm25_results: Results from ``BM25Retriever.search()``.
        top_k: Maximum number of fused results to return.
        k: Standard RRF rank constant. Defaults to 60.

    Returns:
        Deduplicated hybrid results sorted by descending RRF score.

    Raises:
        RRFError: If rankings are missing, invalid, or fusion cannot run.
    """
    started_at = perf_counter()
    if top_k < 1:
        raise RRFError("top_k must be greater than or equal to 1")
    if k != RRF_K:
        raise RRFError(f"RRF k must remain the standard value {RRF_K}")
    if not embedding_results and not bm25_results:
        raise RRFError("Cannot fuse empty retrieval results")

    fused: dict[str, RetrievedAssessment] = {}
    rrf_scores: dict[str, float] = {}
    embedding_scores: dict[str, float] = {}
    bm25_scores: dict[str, float] = {}
    embedding_ranks: dict[str, int] = {}
    bm25_ranks: dict[str, int] = {}

    for result in embedding_results:
        if result.entity_id in embedding_ranks:
            raise RRFError(f"Duplicate embedding result for entity_id={result.entity_id}")
        rank = _valid_rank(result.embedding_rank, "embedding_rank", result.entity_id)
        _merge_result(fused, result)
        rrf_scores[result.entity_id] = rrf_scores.get(result.entity_id, 0.0) + _rrf_score(rank, k)
        embedding_scores[result.entity_id] = (
            result.embedding_score if result.embedding_score is not None else result.score
        )
        embedding_ranks[result.entity_id] = rank

    for result in bm25_results:
        if result.entity_id in bm25_ranks:
            raise RRFError(f"Duplicate BM25 result for entity_id={result.entity_id}")
        rank = _valid_rank(result.bm25_rank, "bm25_rank", result.entity_id)
        _merge_result(fused, result)
        rrf_scores[result.entity_id] = rrf_scores.get(result.entity_id, 0.0) + _rrf_score(rank, k)
        bm25_scores[result.entity_id] = (
            result.bm25_score if result.bm25_score is not None else result.score
        )
        bm25_ranks[result.entity_id] = rank

    ranked_ids = sorted(
        fused,
        key=lambda entity_id: (
            -rrf_scores[entity_id],
            embedding_ranks.get(entity_id, math.inf),
            bm25_ranks.get(entity_id, math.inf),
            entity_id,
        ),
    )

    results: list[RetrievedAssessment] = []
    for final_rank, entity_id in enumerate(ranked_ids[:top_k], start=1):
        base = fused[entity_id]
        rrf_score = rrf_scores[entity_id]
        results.append(
            base.model_copy(
                update={
                    "retrieval_source": "hybrid",
                    "score": rrf_score,
                    "rrf_score": rrf_score,
                    "embedding_score": embedding_scores.get(entity_id),
                    "bm25_score": bm25_scores.get(entity_id),
                    "rank": final_rank,
                    "embedding_rank": embedding_ranks.get(entity_id),
                    "bm25_rank": bm25_ranks.get(entity_id),
                }
            )
        )

    logger.info(
        "RRF fusion completed: embedding=%d bm25=%d fused=%d elapsed_ms=%.2f",
        len(embedding_results),
        len(bm25_results),
        len(results),
        (perf_counter() - started_at) * 1000,
    )
    return results


def _rrf_score(rank: int, k: int) -> float:
    return 1.0 / (k + rank)


def _valid_rank(rank: int | None, field_name: str, entity_id: str) -> int:
    if rank is None or rank < 1:
        raise RRFError(f"{field_name} is required for entity_id={entity_id}")
    return rank


def _merge_result(
    fused: dict[str, RetrievedAssessment],
    result: RetrievedAssessment,
) -> None:
    existing = fused.get(result.entity_id)
    if existing is None:
        fused[result.entity_id] = result
        return

    _validate_metadata_compatibility(existing, result)

    # Prefer the richer metadata record while preserving the first source's
    # stable presentation fields when both are populated.
    updates = {}
    for field in (
        "name",
        "url",
        "test_type",
        "duration",
    ):
        if not getattr(existing, field) and getattr(result, field):
            updates[field] = getattr(result, field)
    for field in ("job_levels", "languages", "keys"):
        if not getattr(existing, field) and getattr(result, field):
            updates[field] = list(getattr(result, field))
    if existing.duration_minutes is None and result.duration_minutes is not None:
        updates["duration_minutes"] = result.duration_minutes
    if updates:
        fused[result.entity_id] = existing.model_copy(update=updates)


def _validate_metadata_compatibility(
    existing: RetrievedAssessment,
    candidate: RetrievedAssessment,
) -> None:
    for field in ("name", "url"):
        existing_value = getattr(existing, field)
        candidate_value = getattr(candidate, field)
        if existing_value and candidate_value and existing_value != candidate_value:
            raise RRFError(
                f"Metadata mismatch for entity_id={existing.entity_id}: {field} differs"
            )
