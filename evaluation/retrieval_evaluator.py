"""Offline retrieval evaluator for BM25, Embedding, and Hybrid retrievers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable

from evaluation.metrics import (
    latency_stats,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "retrieval_eval.json"


@dataclass
class RetrievalExample:
    query: str
    relevant_names: list[str]


@dataclass
class RetrievalMetrics:
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    mrr: float = 0.0
    ndcg_at_10: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    latency: dict = field(default_factory=dict)
    num_queries: int = 0

    def to_dict(self) -> dict:
        return {
            "recall@1": round(self.recall_at_1, 4),
            "recall@3": round(self.recall_at_3, 4),
            "recall@5": round(self.recall_at_5, 4),
            "recall@10": round(self.recall_at_10, 4),
            "mrr": round(self.mrr, 4),
            "ndcg@10": round(self.ndcg_at_10, 4),
            "precision@3": round(self.precision_at_3, 4),
            "precision@5": round(self.precision_at_5, 4),
            "latency_ms": self.latency,
            "num_queries": self.num_queries,
        }


class RetrievalEvaluator:
    """Evaluates a retrieval function against a dataset of queries with known relevant items."""

    def __init__(self, dataset_path: Path | str | None = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET
        self._examples: list[RetrievalExample] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        with self._dataset_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._examples = [
            RetrievalExample(
                query=item["query"],
                relevant_names=item["relevant_names"],
            )
            for item in data
        ]
        logger.info("Retrieval dataset loaded: %d examples", len(self._examples))

    def evaluate(
        self,
        retrieval_fn: Callable[[str], list[str]],
        top_k: int = 10,
    ) -> RetrievalMetrics:
        """
        Evaluate a retrieval function.
        
        retrieval_fn: callable that takes a query string and returns a list of retrieved assessment names.
        """
        r1, r3, r5, r10, mrr_scores, ndcg_scores, p3, p5 = [], [], [], [], [], [], [], []
        latencies_ms = []

        for ex in self._examples:
            relevant = set(ex.relevant_names)

            start = perf_counter()
            retrieved = retrieval_fn(ex.query)
            elapsed_ms = (perf_counter() - start) * 1000
            latencies_ms.append(elapsed_ms)

            r1.append(recall_at_k(relevant, retrieved, 1))
            r3.append(recall_at_k(relevant, retrieved, 3))
            r5.append(recall_at_k(relevant, retrieved, 5))
            r10.append(recall_at_k(relevant, retrieved, 10))
            mrr_scores.append(reciprocal_rank(relevant, retrieved))
            ndcg_scores.append(ndcg_at_k(relevant, retrieved, 10))
            p3.append(precision_at_k(relevant, retrieved, 3))
            p5.append(precision_at_k(relevant, retrieved, 5))

        n = len(self._examples)
        metrics = RetrievalMetrics(
            recall_at_1=sum(r1) / n,
            recall_at_3=sum(r3) / n,
            recall_at_5=sum(r5) / n,
            recall_at_10=sum(r10) / n,
            mrr=sum(mrr_scores) / n,
            ndcg_at_10=sum(ndcg_scores) / n,
            precision_at_3=sum(p3) / n,
            precision_at_5=sum(p5) / n,
            latency=latency_stats(latencies_ms),
            num_queries=n,
        )
        logger.info(
            "Retrieval evaluation completed: recall@10=%.4f mrr=%.4f ndcg@10=%.4f",
            metrics.recall_at_10,
            metrics.mrr,
            metrics.ndcg_at_10,
        )
        return metrics
