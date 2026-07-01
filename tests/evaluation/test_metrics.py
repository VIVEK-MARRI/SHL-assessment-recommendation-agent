"""Tests for evaluation/metrics.py — pure-Python deterministic metric implementations."""

import math
import pytest

from evaluation.metrics import (
    accuracy,
    confusion_matrix,
    dcg_at_k,
    latency_stats,
    macro_f1,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    precision_recall_f1,
    recall_at_k,
    reciprocal_rank,
)


# ── recall_at_k ──────────────────────────────────────────────────────────────

def test_recall_at_k_perfect() -> None:
    relevant = {"a", "b", "c"}
    retrieved = ["a", "b", "c", "d"]
    assert recall_at_k(relevant, retrieved, 3) == 1.0


def test_recall_at_k_partial() -> None:
    relevant = {"a", "b", "c"}
    retrieved = ["a", "x", "x", "b"]
    assert recall_at_k(relevant, retrieved, 4) == pytest.approx(2 / 3)


def test_recall_at_k_zero() -> None:
    relevant = {"a", "b"}
    retrieved = ["x", "y"]
    assert recall_at_k(relevant, retrieved, 2) == 0.0


def test_recall_at_k_empty_relevant() -> None:
    assert recall_at_k(set(), ["a", "b"], 2) == 0.0


# ── precision_at_k ───────────────────────────────────────────────────────────

def test_precision_at_k_perfect() -> None:
    relevant = {"a", "b"}
    retrieved = ["a", "b", "c"]
    assert precision_at_k(relevant, retrieved, 2) == 1.0


def test_precision_at_k_partial() -> None:
    relevant = {"a", "b"}
    retrieved = ["a", "x", "b"]
    assert precision_at_k(relevant, retrieved, 3) == pytest.approx(2 / 3)


def test_precision_at_k_zero_k() -> None:
    assert precision_at_k({"a"}, ["a"], 0) == 0.0


# ── reciprocal_rank ───────────────────────────────────────────────────────────

def test_reciprocal_rank_first() -> None:
    assert reciprocal_rank({"a"}, ["a", "b", "c"]) == 1.0


def test_reciprocal_rank_second() -> None:
    assert reciprocal_rank({"b"}, ["a", "b", "c"]) == pytest.approx(0.5)


def test_reciprocal_rank_not_found() -> None:
    assert reciprocal_rank({"z"}, ["a", "b", "c"]) == 0.0


def test_mean_reciprocal_rank() -> None:
    queries = [
        ({"a"}, ["a", "b"]),  # rr=1.0
        ({"b"}, ["a", "b"]),  # rr=0.5
    ]
    assert mean_reciprocal_rank(queries) == pytest.approx(0.75)


def test_mean_reciprocal_rank_empty() -> None:
    assert mean_reciprocal_rank([]) == 0.0


# ── ndcg_at_k ────────────────────────────────────────────────────────────────

def test_ndcg_perfect() -> None:
    relevant = {"a", "b"}
    retrieved = ["a", "b", "c"]
    assert ndcg_at_k(relevant, retrieved, 2) == 1.0


def test_ndcg_empty_relevant() -> None:
    assert ndcg_at_k(set(), ["a", "b"], 5) == 0.0


def test_ndcg_none_retrieved() -> None:
    relevant = {"a", "b"}
    assert ndcg_at_k(relevant, ["x", "y"], 5) == 0.0


# ── accuracy ─────────────────────────────────────────────────────────────────

def test_accuracy_perfect() -> None:
    assert accuracy(["a", "b", "c"], ["a", "b", "c"]) == 1.0


def test_accuracy_partial() -> None:
    assert accuracy(["a", "b", "x"], ["a", "b", "c"]) == pytest.approx(2 / 3)


def test_accuracy_empty() -> None:
    assert accuracy([], []) == 0.0


# ── precision_recall_f1 ───────────────────────────────────────────────────────

def test_f1_perfect() -> None:
    preds = ["A", "A", "B"]
    labels = ["A", "A", "B"]
    p, r, f1 = precision_recall_f1(preds, labels, "A")
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0


def test_f1_no_tp() -> None:
    p, r, f1 = precision_recall_f1(["B", "B"], ["A", "A"], "A")
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


# ── confusion_matrix ─────────────────────────────────────────────────────────

def test_confusion_matrix() -> None:
    preds = ["A", "B", "A"]
    labels = ["A", "A", "B"]
    classes = ["A", "B"]
    matrix = confusion_matrix(preds, labels, classes)
    assert matrix["A"]["A"] == 1  # actual A, predicted A
    assert matrix["A"]["B"] == 1  # actual A, predicted B
    assert matrix["B"]["A"] == 1  # actual B, predicted A
    assert matrix["B"]["B"] == 0


# ── latency_stats ─────────────────────────────────────────────────────────────

def test_latency_stats() -> None:
    lats = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = latency_stats(lats)
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0
    assert stats["avg"] == pytest.approx(30.0)
    assert stats["median"] == pytest.approx(30.0)
    assert stats["p95"] == 50.0


def test_latency_stats_empty() -> None:
    stats = latency_stats([])
    assert all(v == 0.0 for v in stats.values())
