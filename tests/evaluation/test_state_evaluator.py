"""Tests for evaluation/state_evaluator.py."""

import json
import pytest
from pathlib import Path

from evaluation.state_evaluator import StateEvaluator


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    path = tmp_path / "conversation_eval.json"
    data = [
        {
            "conversation": [{"role": "user", "content": "Python test for seniors."}],
            "expected_state": {
                "intent": "recommend",
                "scope_flag": "recommend",
                "job_levels": ["senior"],
                "languages": [],
                "mentioned_assessment_names": [],
                "is_comparison_request": False,
                "end_of_conversation": False,
            },
        },
    ]
    path.write_text(json.dumps(data))
    return path


def test_perfect_extraction(dataset: Path) -> None:
    ev = StateEvaluator(dataset_path=dataset)

    def perfect_fn(conv):
        return {
            "intent": "recommend",
            "scope_flag": "recommend",
            "job_levels": ["senior"],
            "languages": [],
            "mentioned_assessment_names": [],
            "is_comparison_request": False,
            "end_of_conversation": False,
        }

    metrics = ev.evaluate(perfect_fn)
    assert metrics.overall_accuracy == pytest.approx(1.0)
    assert metrics.json_valid_rate == 1.0


def test_failed_extraction(dataset: Path) -> None:
    ev = StateEvaluator(dataset_path=dataset)

    def broken_fn(conv):
        raise ValueError("extraction failed")

    metrics = ev.evaluate(broken_fn)
    assert metrics.json_valid_rate == 0.0
    assert metrics.overall_accuracy == 0.0


def test_partial_extraction(dataset: Path) -> None:
    ev = StateEvaluator(dataset_path=dataset)

    def partial_fn(conv):
        return {
            "intent": "recommend",
            "scope_flag": "recommend",
            "job_levels": [],        # wrong
            "languages": [],
            "mentioned_assessment_names": [],
            "is_comparison_request": False,
            "end_of_conversation": False,
        }

    metrics = ev.evaluate(partial_fn)
    # 6 out of 7 fields correct
    assert 0.0 < metrics.overall_accuracy < 1.0


def test_metrics_to_dict(dataset: Path) -> None:
    ev = StateEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda conv: {})
    d = metrics.to_dict()
    assert "field_accuracy" in d
    assert "overall_accuracy" in d
    assert "json_valid_rate" in d
    assert "latency_ms" in d
