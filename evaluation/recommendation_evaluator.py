"""Offline recommendation evaluator: generated names vs expected assessments."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from evaluation.metrics import precision_at_k, recall_at_k

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "recommendation_eval.json"


@dataclass
class RecommendationExample:
    conversation: list[dict]
    expected_names: list[str]


@dataclass
class RecommendationMetrics:
    exact_match: float = 0.0         # all expected names present exactly
    top_3_accuracy: float = 0.0       # ≥1 expected in top-3
    top_5_accuracy: float = 0.0       # ≥1 expected in top-5
    precision: float = 0.0            # avg precision over all queries
    recall: float = 0.0              # avg recall over all queries
    avg_recommendation_count: float = 0.0
    num_examples: int = 0

    def to_dict(self) -> dict:
        return {
            "exact_match": round(self.exact_match, 4),
            "top_3_accuracy": round(self.top_3_accuracy, 4),
            "top_5_accuracy": round(self.top_5_accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "avg_recommendation_count": round(self.avg_recommendation_count, 2),
            "num_examples": self.num_examples,
        }


class RecommendationEvaluator:
    """Evaluates a recommendation function against labelled expected outputs."""

    def __init__(self, dataset_path: Path | str | None = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET
        self._examples: list[RecommendationExample] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        with self._dataset_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._examples = [
            RecommendationExample(
                conversation=item["conversation"],
                expected_names=item["expected_names"],
            )
            for item in data
        ]
        logger.info("Recommendation dataset loaded: %d examples", len(self._examples))

    def evaluate(
        self, recommend_fn: Callable[[list[dict]], list[str]]
    ) -> RecommendationMetrics:
        """
        Evaluate a recommendation callable.
        recommend_fn: takes a conversation list and returns list of recommended assessment names.
        """
        exact_matches = 0
        top3_hits = 0
        top5_hits = 0
        precisions = []
        recalls = []
        rec_counts = []

        for ex in self._examples:
            expected_set = {n.lower() for n in ex.expected_names}
            try:
                predicted = recommend_fn(ex.conversation)
            except Exception as e:
                logger.warning("Recommendation failed: %s", e)
                predicted = []

            predicted_lower = [n.lower() for n in predicted]
            rec_counts.append(len(predicted))

            # Exact match: all expected names present in predicted (order-independent)
            if expected_set and expected_set.issubset(set(predicted_lower)):
                exact_matches += 1

            # Top-3 / Top-5 accuracy: at least one expected name in top-K
            if any(n in expected_set for n in predicted_lower[:3]):
                top3_hits += 1
            if any(n in expected_set for n in predicted_lower[:5]):
                top5_hits += 1

            # Precision and recall treating retrieval as the predicted list
            prec = precision_at_k(expected_set, predicted_lower, len(predicted))
            rec = recall_at_k(expected_set, predicted_lower, len(predicted))
            precisions.append(prec)
            recalls.append(rec)

        n = len(self._examples)
        metrics = RecommendationMetrics(
            exact_match=exact_matches / n if n else 0.0,
            top_3_accuracy=top3_hits / n if n else 0.0,
            top_5_accuracy=top5_hits / n if n else 0.0,
            precision=sum(precisions) / n if n else 0.0,
            recall=sum(recalls) / n if n else 0.0,
            avg_recommendation_count=sum(rec_counts) / n if n else 0.0,
            num_examples=n,
        )
        logger.info(
            "Recommendation evaluation completed: exact_match=%.4f recall=%.4f precision=%.4f",
            metrics.exact_match,
            metrics.recall,
            metrics.precision,
        )
        return metrics
