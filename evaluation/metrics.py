"""Deterministic metric implementations for the evaluation harness.

All implementations are pure Python — no sklearn dependencies.
"""

from __future__ import annotations

import math
import statistics
from typing import Sequence


# ── Retrieval Metrics ─────────────────────────────────────────────────────────

def recall_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Recall@K: fraction of relevant items appearing in the top-K retrieved."""
    if not relevant:
        return 0.0
    hits = sum(1 for item in retrieved[:k] if item in relevant)
    return hits / len(relevant)


def precision_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Precision@K: fraction of top-K retrieved items that are relevant."""
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / k


def reciprocal_rank(relevant: set[str], retrieved: list[str]) -> float:
    """Reciprocal Rank: 1/rank of the first relevant item, 0 if none found."""
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(queries: list[tuple[set[str], list[str]]]) -> float:
    """Mean Reciprocal Rank over a list of (relevant_set, retrieved_list) pairs."""
    if not queries:
        return 0.0
    return sum(reciprocal_rank(rel, ret) for rel, ret in queries) / len(queries)


def dcg_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Discounted Cumulative Gain at K."""
    dcg = 0.0
    for rank, item in enumerate(retrieved[:k], start=1):
        if item in relevant:
            dcg += 1.0 / math.log2(rank + 1)
    return dcg


def ndcg_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Normalized DCG at K."""
    actual = dcg_at_k(relevant, retrieved, k)
    ideal_retrieved = list(relevant)[:k]
    ideal = dcg_at_k(relevant, ideal_retrieved, k)
    if ideal == 0.0:
        return 0.0
    return actual / ideal


# ── Classification Metrics ────────────────────────────────────────────────────

def accuracy(predictions: list[str], labels: list[str]) -> float:
    """Fraction of predictions matching their labels exactly."""
    if not labels:
        return 0.0
    correct = sum(p == l for p, l in zip(predictions, labels))
    return correct / len(labels)


def precision_recall_f1(
    predictions: list[str],
    labels: list[str],
    positive_class: str,
) -> tuple[float, float, float]:
    """Precision, Recall, F1 for a binary (one-vs-rest) positive class."""
    tp = sum(1 for p, l in zip(predictions, labels) if p == positive_class and l == positive_class)
    fp = sum(1 for p, l in zip(predictions, labels) if p == positive_class and l != positive_class)
    fn = sum(1 for p, l in zip(predictions, labels) if p != positive_class and l == positive_class)

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def confusion_matrix(
    predictions: list[str],
    labels: list[str],
    classes: list[str],
) -> dict[str, dict[str, int]]:
    """Build a confusion matrix as a nested dict: matrix[actual][predicted]."""
    matrix: dict[str, dict[str, int]] = {c: {c2: 0 for c2 in classes} for c in classes}
    for pred, label in zip(predictions, labels):
        if label in matrix and pred in matrix[label]:
            matrix[label][pred] += 1
    return matrix


def macro_f1(predictions: list[str], labels: list[str], classes: list[str]) -> float:
    """Macro-averaged F1 across all classes."""
    if not classes:
        return 0.0
    f1_scores = []
    for cls in classes:
        _, _, f1 = precision_recall_f1(predictions, labels, cls)
        f1_scores.append(f1)
    return sum(f1_scores) / len(f1_scores)


# ── Latency Statistics ────────────────────────────────────────────────────────

def latency_stats(latencies_ms: list[float]) -> dict[str, float]:
    """Compute avg, median, P95, P99, min, max from a list of latency values."""
    if not latencies_ms:
        return {"avg": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0}

    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)

    def percentile(p: float) -> float:
        idx = int(math.ceil(n * p / 100.0)) - 1
        return sorted_lat[max(0, min(idx, n - 1))]

    return {
        "avg": statistics.mean(latencies_ms),
        "median": statistics.median(latencies_ms),
        "p95": percentile(95),
        "p99": percentile(99),
        "min": sorted_lat[0],
        "max": sorted_lat[-1],
    }
