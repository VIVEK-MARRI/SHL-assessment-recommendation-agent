"""Tests for evaluation/retrieval_evaluator.py."""

import json
import pytest
from pathlib import Path

from evaluation.retrieval_evaluator import RetrievalEvaluator


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    path = tmp_path / "retrieval_eval.json"
    data = [
        {"query": "Python test", "relevant_names": ["Python (New)", "Python Basics"]},
        {"query": "Java test", "relevant_names": ["Core Java"]},
    ]
    path.write_text(json.dumps(data))
    return path


def test_perfect_retrieval(dataset: Path) -> None:
    ev = RetrievalEvaluator(dataset_path=dataset)

    def perfect_fn(query: str) -> list[str]:
        return ["Python (New)", "Python Basics", "Core Java"]

    metrics = ev.evaluate(perfect_fn)
    assert metrics.recall_at_1 > 0.0
    assert metrics.recall_at_3 > 0.0
    assert metrics.mrr > 0.0
    assert metrics.num_queries == 2


def test_zero_retrieval(dataset: Path) -> None:
    ev = RetrievalEvaluator(dataset_path=dataset)

    metrics = ev.evaluate(lambda q: [])
    assert metrics.recall_at_1 == 0.0
    assert metrics.mrr == 0.0
    assert metrics.ndcg_at_10 == 0.0


def test_metrics_to_dict(dataset: Path) -> None:
    ev = RetrievalEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda q: [])
    d = metrics.to_dict()
    assert "recall@1" in d
    assert "mrr" in d
    assert "ndcg@10" in d
    assert "latency_ms" in d


def test_latency_recorded(dataset: Path) -> None:
    ev = RetrievalEvaluator(dataset_path=dataset)
    metrics = ev.evaluate(lambda q: [])
    assert metrics.latency["avg"] >= 0.0
