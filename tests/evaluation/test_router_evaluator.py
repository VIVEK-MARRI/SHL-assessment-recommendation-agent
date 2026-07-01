"""Tests for evaluation/router_evaluator.py."""

import json
import pytest
from pathlib import Path

from evaluation.router_evaluator import RouterEvaluator


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    path = tmp_path / "routing_eval.json"
    data = [
        {"conversation": [{"role": "user", "content": "Python test"}], "expected_route": "RECOMMEND"},
        {"conversation": [{"role": "user", "content": "Compare A and B"}], "expected_route": "COMPARE"},
        {"conversation": [{"role": "user", "content": "I need a test"}], "expected_route": "CLARIFY"},
    ]
    path.write_text(json.dumps(data))
    return path


def test_perfect_routing(dataset: Path) -> None:
    ev = RouterEvaluator(dataset_path=dataset)

    def perfect_fn(conv):
        text = conv[0]["content"].lower()
        if "compare" in text:
            return "COMPARE"
        if "python" in text:
            return "RECOMMEND"
        return "CLARIFY"

    metrics = ev.evaluate(perfect_fn)
    assert metrics.accuracy == 1.0
    assert metrics.num_examples == 3


def test_all_wrong_routing(dataset: Path) -> None:
    ev = RouterEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: "REFUSE")
    assert metrics.accuracy == 0.0


def test_metrics_to_dict(dataset: Path) -> None:
    ev = RouterEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: "RECOMMEND")
    d = metrics.to_dict()
    assert "accuracy" in d
    assert "macro_f1" in d
    assert "confusion_matrix" in d
    assert "per_class" in d


def test_confusion_matrix_populated(dataset: Path) -> None:
    ev = RouterEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: "RECOMMEND")
    # All predicted as RECOMMEND, so the RECOMMEND row should have entries
    assert "RECOMMEND" in metrics.confusion
