"""Offline state extraction evaluator: extracted fields vs expected ground truth."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable

from evaluation.metrics import latency_stats

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "conversation_eval.json"

# Fields to compare between extracted and expected ConversationState dicts
_COMPARABLE_FIELDS = [
    "intent",
    "scope_flag",
    "job_levels",
    "languages",
    "mentioned_assessment_names",
    "is_comparison_request",
    "end_of_conversation",
]


@dataclass
class StateExample:
    conversation: list[dict]
    expected_state: dict


@dataclass
class StateMetrics:
    field_accuracy: dict = field(default_factory=dict)  # per-field accuracy
    overall_accuracy: float = 0.0
    json_valid_rate: float = 1.0
    latency: dict = field(default_factory=dict)
    num_examples: int = 0

    def to_dict(self) -> dict:
        return {
            "field_accuracy": {k: round(v, 4) for k, v in self.field_accuracy.items()},
            "overall_accuracy": round(self.overall_accuracy, 4),
            "json_valid_rate": round(self.json_valid_rate, 4),
            "latency_ms": self.latency,
            "num_examples": self.num_examples,
        }


class StateEvaluator:
    """Evaluates a state extraction callable against labelled conversation data."""

    def __init__(self, dataset_path: Path | str | None = None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET
        self._examples: list[StateExample] = []
        self._load_dataset()

    def _load_dataset(self) -> None:
        with self._dataset_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self._examples = [
            StateExample(
                conversation=item["conversation"],
                expected_state=item["expected_state"],
            )
            for item in data
        ]
        logger.info("State dataset loaded: %d examples", len(self._examples))

    def evaluate(self, extract_fn: Callable[[list[dict]], dict]) -> StateMetrics:
        """
        Evaluate a state extraction function.
        extract_fn: callable that takes a list of conversation message dicts
                    and returns a dict representing the ConversationState.
        """
        field_hits: dict[str, int] = {f: 0 for f in _COMPARABLE_FIELDS}
        total = 0
        json_valid = 0
        latencies_ms = []

        for ex in self._examples:
            total += 1
            start = perf_counter()
            try:
                extracted = extract_fn(ex.conversation)
                json_valid += 1
            except Exception as e:
                logger.warning("State extraction failed: %s", e)
                latencies_ms.append((perf_counter() - start) * 1000)
                continue
            latencies_ms.append((perf_counter() - start) * 1000)

            for f in _COMPARABLE_FIELDS:
                exp_val = ex.expected_state.get(f)
                got_val = extracted.get(f)
                # Normalize list comparisons to sets for order-independence
                if isinstance(exp_val, list) and isinstance(got_val, list):
                    if set(str(v).lower() for v in exp_val) == set(str(v).lower() for v in got_val):
                        field_hits[f] += 1
                elif str(exp_val).lower() == str(got_val).lower():
                    field_hits[f] += 1

        field_accuracy = {
            f: field_hits[f] / total if total else 0.0 for f in _COMPARABLE_FIELDS
        }
        overall = sum(field_accuracy.values()) / len(field_accuracy) if field_accuracy else 0.0
        json_valid_rate = json_valid / total if total else 0.0

        metrics = StateMetrics(
            field_accuracy=field_accuracy,
            overall_accuracy=overall,
            json_valid_rate=json_valid_rate,
            latency=latency_stats(latencies_ms),
            num_examples=total,
        )
        logger.info(
            "State evaluation completed: overall_accuracy=%.4f json_valid_rate=%.4f",
            metrics.overall_accuracy,
            metrics.json_valid_rate,
        )
        return metrics
