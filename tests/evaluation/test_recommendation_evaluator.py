"""Tests for evaluation/recommendation_evaluator.py."""

import json
import pytest
from pathlib import Path

from evaluation.recommendation_evaluator import RecommendationEvaluator


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    path = tmp_path / "recommendation_eval.json"
    data = [
        {
            "conversation": [{"role": "user", "content": "Python assessment"}],
            "expected_names": ["Python (New)", "Python Basics"],
        },
        {
            "conversation": [{"role": "user", "content": "Cognitive test"}],
            "expected_names": ["Verify - G+ General Ability"],
        },
    ]
    path.write_text(json.dumps(data))
    return path


def test_perfect_recommendation(dataset: Path) -> None:
    ev = RecommendationEvaluator(dataset_path=dataset)

    def perfect_fn(conv):
        return ["Python (New)", "Python Basics", "Verify - G+ General Ability"]

    metrics = ev.evaluate(perfect_fn)
    assert metrics.exact_match == 1.0
    assert metrics.top_3_accuracy == 1.0
    assert metrics.num_examples == 2


def test_zero_recommendations(dataset: Path) -> None:
    ev = RecommendationEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: [])
    assert metrics.exact_match == 0.0
    assert metrics.top_3_accuracy == 0.0
    assert metrics.avg_recommendation_count == 0.0


def test_partial_recommendations(dataset: Path) -> None:
    ev = RecommendationEvaluator(dataset_path=dataset)

    def partial_fn(conv):
        return ["Python (New)", "Java Test"]

    metrics = ev.evaluate(partial_fn)
    assert 0.0 <= metrics.exact_match <= 1.0
    assert metrics.avg_recommendation_count == pytest.approx(2.0)


def test_metrics_to_dict(dataset: Path) -> None:
    ev = RecommendationEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: [])
    d = metrics.to_dict()
    assert "exact_match" in d
    assert "top_3_accuracy" in d
    assert "top_5_accuracy" in d
    assert "precision" in d
    assert "recall" in d
    assert "avg_recommendation_count" in d
