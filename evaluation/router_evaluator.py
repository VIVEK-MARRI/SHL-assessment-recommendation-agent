"""Offline router evaluator: predicted routes vs expected routes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from evaluation.metrics import accuracy, confusion_matrix, macro_f1, precision_recall_f1

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "routing_eval.json"

_ROUTE_CLASSES = ["RECOMMEND", "REFINE", "COMPARE", "CLARIFY", "REFUSE"]


@dataclass
class RoutingExample:
    conversation: list[dict]
    expected_route: str


@dataclass
class RouterMetrics:
    accuracy: float = 0.0
    macro_f1: float = 0.0
    per_class: dict = field(default_factory=dict)
    confusion: dict = field(default_factory=dict)
    num_examples: int = 0

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "macro_f1": round(self.macro_f1, 4),
            "per_class": self.per_class,
            "confusion_matrix": self.confusion,
            "num_examples": self.num_examples,
        }


class RouterEvaluator:
    """Evaluates a routing callable against a labelled dataset."""

    def __init__(self, dataset_path: Path | str | None = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET
        self._examples: list[RoutingExample] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        with self._dataset_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._examples = [
            RoutingExample(
                conversation=item["conversation"],
                expected_route=item["expected_route"].upper(),
            )
            for item in data
        ]
        logger.info("Routing dataset loaded: %d examples", len(self._examples))

    def evaluate(self, route_fn: Callable[[list[dict]], str]) -> RouterMetrics:
        """
        Evaluate a routing function.
        route_fn: callable that takes a list of conversation message dicts and returns the route string.
        """
        predictions = []
        labels = []

        for ex in self._examples:
            predicted = route_fn(ex.conversation).upper()
            predictions.append(predicted)
            labels.append(ex.expected_route)

        acc = accuracy(predictions, labels)
        mf1 = macro_f1(predictions, labels, _ROUTE_CLASSES)
        conf = confusion_matrix(predictions, labels, _ROUTE_CLASSES)

        per_class = {}
        for cls in _ROUTE_CLASSES:
            prec, rec, f1 = precision_recall_f1(predictions, labels, cls)
            per_class[cls] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
            }

        metrics = RouterMetrics(
            accuracy=acc,
            macro_f1=mf1,
            per_class=per_class,
            confusion=conf,
            num_examples=len(self._examples),
        )
        logger.info(
            "Router evaluation completed: accuracy=%.4f macro_f1=%.4f",
            metrics.accuracy,
            metrics.macro_f1,
        )
        return metrics
