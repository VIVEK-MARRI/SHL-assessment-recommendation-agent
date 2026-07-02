"""Benchmark runner — evaluates retrieval performance against ground-truth."""
from __future__ import annotations
import json, logging, sys, time
from pathlib import Path
from collections import Counter
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.WARNING)

import numpy as np
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.retrieval_models import RetrievedAssessment

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def precision_at_k(relevant: set[str], retrieved: list[RetrievedAssessment], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    hits = sum(1 for r in top if r.entity_id in relevant)
    return hits / k if relevant else 1.0

def recall_at_k(relevant: set[str], retrieved: list[RetrievedAssessment], k: int) -> float:
    top = retrieved[:k]
    if not relevant:
        return 1.0
    hits = sum(1 for r in top if r.entity_id in relevant)
    return hits / len(relevant)

def mrr(relevant: set[str], retrieved: list[RetrievedAssessment]) -> float:
    for i, r in enumerate(retrieved, start=1):
        if r.entity_id in relevant:
            return 1.0 / i
    return 0.0

def ndcg_at_k(relevant: set[str], retrieved: list[RetrievedAssessment], k: int) -> float:
    """Computes NDCG@k with binary relevance."""
    k = min(k, len(retrieved))
    if k == 0:
        return 0.0
    dcg = 0.0
    for i, r in enumerate(retrieved[:k], start=1):
        rel = 1.0 if r.entity_id in relevant else 0.0
        dcg += rel / np.log2(i + 1) if i > 1 else rel
    ideal_rel = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 1) for i in range(1, ideal_rel + 1)) if ideal_rel > 0 else 0.0
    idcg += 1.0 if ideal_rel >= 1 else 0.0  # first element
    # Actually let's recalc properly
    dcg = 0.0
    for i in range(k):
        rel = 1.0 if retrieved[i].entity_id in relevant else 0.0
        dcg += (2**rel - 1) / np.log2(i + 2)
    ideal = sorted(relevant)[:k]
    idcg = 0.0
    for i in range(k):
        rel = 1.0 if i < len(relevant) else 0.0
        idcg += (2**rel - 1) / np.log2(i + 2)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def contamination_score(relevant: set[str], retrieved: list[RetrievedAssessment], contaminant_ids: set[str]) -> float:
    """Fraction of top-k results that are contaminant assessments."""
    if not contaminant_ids:
        return 0.0
    top = retrieved[:10]
    return sum(1 for r in top if r.entity_id in contaminant_ids) / len(top)

# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(benchmark_path: Path, tag: str = "baseline", top_k: int = 20) -> dict:
    """Run benchmark, return metrics."""
    with open(benchmark_path, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"\n{'='*60}")
    print(f"  BENCHMARK: {tag}  ({len(queries)} queries)")
    print(f"{'='*60}")

    retriever = HybridRetriever()
    retriever.initialize()

    all_metrics = {
        "p@1": [], "p@3": [], "p@5": [], "p@10": [],
        "r@10": [], "mrr": [], "ndcg@10": [],
        "latency_ms": [], "coverage": set(),
        "contaminations": [],
    }
    cat_metrics: dict[str, dict] = {}
    failures = []

    for i, entry in enumerate(queries):
        query = entry["query"]
        relevant = set(entry["relevant_ids"])
        category = entry["category"]

        if category not in cat_metrics:
            cat_metrics[category] = {
                "p@1": [], "p@3": [], "p@5": [], "p@10": [],
                "r@10": [], "mrr": [], "ndcg@10": [], "count": 0,
            }
        cat_metrics[category]["count"] += 1

        start = time.perf_counter()
        try:
            result = retriever.search(query, top_k=top_k)
            retrieved = result.results
        except Exception as e:
            failures.append({"query": query, "error": str(e)})
            continue
        latency = (time.perf_counter() - start) * 1000
        all_metrics["latency_ms"].append(latency)

        retrieved_entity_ids = [r.entity_id for r in retrieved]
        all_metrics["coverage"].update(retrieved_entity_ids)

        p1 = precision_at_k(relevant, retrieved, 1)
        p3 = precision_at_k(relevant, retrieved, 3)
        p5 = precision_at_k(relevant, retrieved, 5)
        p10 = precision_at_k(relevant, retrieved, 10)
        r10 = recall_at_k(relevant, retrieved, 10)
        mrr_val = mrr(relevant, retrieved)
        ndcg_val = ndcg_at_k(relevant, retrieved, 10)

        all_metrics["p@1"].append(p1)
        all_metrics["p@3"].append(p3)
        all_metrics["p@5"].append(p5)
        all_metrics["p@10"].append(p10)
        all_metrics["r@10"].append(r10)
        all_metrics["mrr"].append(mrr_val)
        all_metrics["ndcg@10"].append(ndcg_val)

        for m in [cat_metrics[category]["p@1"], cat_metrics[category]["p@3"],
                  cat_metrics[category]["p@5"], cat_metrics[category]["p@10"],
                  cat_metrics[category]["r@10"], cat_metrics[category]["mrr"],
                  cat_metrics[category]["ndcg@10"]]:
            pass  # will fill below

        cat_metrics[category]["p@1"].append(p1)
        cat_metrics[category]["p@3"].append(p3)
        cat_metrics[category]["p@5"].append(p5)
        cat_metrics[category]["p@10"].append(p10)
        cat_metrics[category]["r@10"].append(r10)
        cat_metrics[category]["mrr"].append(mrr_val)
        cat_metrics[category]["ndcg@10"].append(ndcg_val)

        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(queries)}")

    # Aggregate
    summary = {
        "tag": tag,
        "num_queries": len(queries) - len(failures),
        "failures": len(failures),
        "precision@1": float(np.mean(all_metrics["p@1"])),
        "precision@3": float(np.mean(all_metrics["p@3"])),
        "precision@5": float(np.mean(all_metrics["p@5"])),
        "precision@10": float(np.mean(all_metrics["p@10"])),
        "recall@10": float(np.mean(all_metrics["r@10"])),
        "mrr": float(np.mean(all_metrics["mrr"])),
        "ndcg@10": float(np.mean(all_metrics["ndcg@10"])),
        "avg_latency_ms": float(np.mean(all_metrics["latency_ms"])),
        "p95_latency_ms": float(np.percentile(all_metrics["latency_ms"], 95)),
        "unique_assessments_retrieved": len(all_metrics["coverage"]),
        "total_assessments": 377,
        "coverage_pct": round(len(all_metrics["coverage"]) / 377 * 100, 1),
    }

    cat_summary = {}
    for cat, m in sorted(cat_metrics.items()):
        if m["count"] > 0:
            cat_summary[cat] = {
                "count": m["count"],
                "precision@1": float(np.mean(m["p@1"])),
                "precision@3": float(np.mean(m["p@3"])),
                "precision@5": float(np.mean(m["p@5"])),
                "recall@10": float(np.mean(m["r@10"])),
                "mrr": float(np.mean(m["mrr"])),
            }

    print(f"\n  RESULTS ({tag}):")
    print(f"  Queries: {summary['num_queries']} (failures: {summary['failures']})")
    print(f"  Precision@1:  {summary['precision@1']:.4f}")
    print(f"  Precision@3:  {summary['precision@3']:.4f}")
    print(f"  Precision@5:  {summary['precision@5']:.4f}")
    print(f"  Precision@10: {summary['precision@10']:.4f}")
    print(f"  Recall@10:    {summary['recall@10']:.4f}")
    print(f"  MRR:          {summary['mrr']:.4f}")
    print(f"  NDCG@10:      {summary['ndcg@10']:.4f}")
    print(f"  Avg Latency:  {summary['avg_latency_ms']:.2f}ms")
    print(f"  P95 Latency:  {summary['p95_latency_ms']:.2f}ms")
    print(f"  Coverage:     {summary['unique_assessments_retrieved']}/{summary['total_assessments']} ({summary['coverage_pct']}%)")

    return {"summary": summary, "cat_summary": cat_summary, "failures": failures}

if __name__ == "__main__":
    benchmark_path = ROOT / "benchmark" / "retrieval_benchmark.json"
    results = run_benchmark(benchmark_path, tag="baseline")
    (ROOT / "benchmark" / "baseline_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nResults saved to benchmark/baseline_results.json")
