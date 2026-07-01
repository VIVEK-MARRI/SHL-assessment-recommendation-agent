"""Confidence evaluation for hybrid retrieval results."""

from __future__ import annotations

import logging

from retrieval.retrieval_models import HybridRetrievalResult, RetrievedAssessment

logger = logging.getLogger(__name__)


class ConfidenceGateError(Exception):
    """Raised when hybrid confidence cannot be evaluated."""


class ConfidenceGate:
    """Evaluate whether fused retrieval evidence is strong enough."""

    def __init__(
        self,
        minimum_rrf_score: float = 0.02,
        minimum_overlap: int = 1,
        minimum_results: int = 1,
    ) -> None:
        """Create a confidence gate with deterministic thresholds."""
        if minimum_rrf_score < 0:
            raise ConfidenceGateError("minimum_rrf_score must be non-negative")
        if minimum_overlap < 0:
            raise ConfidenceGateError("minimum_overlap must be non-negative")
        if minimum_results < 1:
            raise ConfidenceGateError("minimum_results must be greater than or equal to 1")
        self.minimum_rrf_score = minimum_rrf_score
        self.minimum_overlap = minimum_overlap
        self.minimum_results = minimum_results

    def evaluate(
        self,
        results: list[RetrievedAssessment],
        embedding_results: list[RetrievedAssessment],
        bm25_results: list[RetrievedAssessment],
    ) -> HybridRetrievalResult:
        """Return confidence metadata for fused hybrid results."""
        if not results:
            raise ConfidenceGateError("Cannot evaluate empty hybrid results")

        top_score = results[0].rrf_score
        if top_score is None:
            raise ConfidenceGateError("Top result is missing rrf_score")

        embedding_ids = {result.entity_id for result in embedding_results}
        bm25_ids = {result.entity_id for result in bm25_results}
        overlap = len(embedding_ids & bm25_ids)

        if len(results) < self.minimum_results:
            confidence = "LOW"
            reason = "Insufficient evidence"
        elif top_score < self.minimum_rrf_score:
            confidence = "LOW"
            reason = "Insufficient evidence"
        elif overlap == 0:
            confidence = "LOW"
            reason = "Insufficient evidence"
        elif overlap >= self.minimum_overlap:
            confidence = "HIGH"
            reason = "Strong agreement"
        elif len(embedding_results) < len(bm25_results):
            confidence = "MEDIUM"
            reason = "Weak semantic support"
        else:
            confidence = "MEDIUM"
            reason = "Weak lexical support"

        logger.info(
            "Confidence evaluation completed: confidence=%s reason=%s overlap=%d",
            confidence,
            reason,
            overlap,
        )
        return HybridRetrievalResult(results=results, confidence=confidence, reason=reason)
