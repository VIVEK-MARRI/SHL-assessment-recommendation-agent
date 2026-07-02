"""Comprehensive retrieval audit: full coverage, stress test, false positives, failure analysis."""
from __future__ import annotations
import json, logging, sys, time, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.WARNING)

from agent.conversation_models import ConversationState
from agent.query_builder import QueryBuilder
from agent.query_models import QueryFilters
from agent.routing_models import RouteType, RoutingDecision
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.retrieval_models import RetrievedAssessment

# --- Metrics helpers ---
def precision_at_k(relevant: set[str], retrieved, k: int) -> float:
    top = retrieved[:k]
    if not top or not relevant:
        return 0.0
    hits = sum(1 for r in top if r.entity_id in relevant)
    return hits / k

def recall_at_k(relevant: set[str], retrieved, k: int) -> float:
    if not relevant:
        return 1.0
    hits = sum(1 for r in retrieved[:k] if r.entity_id in relevant)
    return hits / len(relevant)

def mrr(relevant: set[str], retrieved) -> float:
    for i, r in enumerate(retrieved):
        if r.entity_id in relevant:
            return 1.0 / (i + 1)
    return 0.0

def ndcg_at_k(relevant: set[str], retrieved, k: int) -> float:
    if not relevant:
        return 0.0
    dcg = 0.0
    for i, r in enumerate(retrieved[:k]):
        rel = 1.0 if r.entity_id in relevant else 0.0
        if i == 0:
            dcg += rel
        else:
            dcg += rel / (i + 1)  # log2(i+1) approximation
    # Ideal DCG
    ideal = sum(1.0 / (i + 1) for i in range(min(k, len(relevant))))
    return dcg / ideal if ideal > 0 else 0.0

def rank_of_first_relevant(relevant: set[str], retrieved) -> int | None:
    for i, r in enumerate(retrieved):
        if r.entity_id in relevant:
            return i + 1
    return None

# --- Load benchmarks ---
def load_benchmark(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        return json.load(f)

# --- Run benchmark ---
def run_benchmark(queries: list[dict], retriever, qb, decision, tag: str) -> dict:
    """Run retrieval for all queries, return detailed results."""
    
    per_query_results = []
    all_metrics = {"p@1":[], "p@3":[], "p@5":[], "p@10":[], "r@10":[], "mrr":[], "ndcg@10":[], "latency_ms":[], "ranks":[]}
    cat_metrics = {}
    coverage = set()
    
    for i, entry in enumerate(queries):
        query_text = entry["query"]
        relevant = set(entry["relevant_ids"])
        category = entry.get("category", "general")
        
        if category not in cat_metrics:
            cat_metrics[category] = {"p@1":[], "p@3":[], "p@5":[], "p@10":[], "r@10":[], "mrr":[], "ndcg@10":[], "count":0, "ranks":[]}
        cat_metrics[category]["count"] += 1
        
        # Build retrieval query using QueryBuilder with minimal state
        state = ConversationState()
        try:
            retrieval_query = qb.build(state, decision)
        except Exception:
            # Fallback: use raw query text
            query_for_retrieval = query_text
            filters = QueryFilters()
        else:
            query_for_retrieval = retrieval_query.query_text or query_text
            filters = retrieval_query.filters
        
        # If query text is empty (or too short), use raw query
        if len(query_for_retrieval.strip()) < 2:
            query_for_retrieval = query_text
        
        # Retrieve
        start = time.perf_counter()
        try:
            result = retriever.search(
                query_for_retrieval,
                state=ConversationState(),
                filters=QueryFilters(),
                top_k=20,
            )
            retrieved = result.results
        except Exception as e:
            # Fallback without state
            try:
                result = retriever.search(query_for_retrieval, top_k=20)
                retrieved = result.results
            except Exception as e2:
                print(f"  WARN: Search failed for '{query_text[:50]}': {e2}")
                continue
        
        latency = (time.perf_counter() - start) * 1000
        all_metrics["latency_ms"].append(latency)
        coverage.update(r.entity_id for r in retrieved)
        
        p1 = precision_at_k(relevant, retrieved, 1)
        p3 = precision_at_k(relevant, retrieved, 3)
        p5 = precision_at_k(relevant, retrieved, 5)
        p10 = precision_at_k(relevant, retrieved, 10)
        r10 = recall_at_k(relevant, retrieved, 10)
        mrr_val = mrr(relevant, retrieved)
        ndcg_val = ndcg_at_k(relevant, retrieved, 10)
        first_rank = rank_of_first_relevant(relevant, retrieved)
        
        all_metrics["p@1"].append(p1)
        all_metrics["p@3"].append(p3)
        all_metrics["p@5"].append(p5)
        all_metrics["p@10"].append(p10)
        all_metrics["r@10"].append(r10)
        all_metrics["mrr"].append(mrr_val)
        all_metrics["ndcg@10"].append(ndcg_val)
        if first_rank is not None:
            all_metrics["ranks"].append(first_rank)
        
        cat_metrics[category]["p@1"].append(p1)
        cat_metrics[category]["p@3"].append(p3)
        cat_metrics[category]["p@5"].append(p5)
        cat_metrics[category]["p@10"].append(p10)
        cat_metrics[category]["r@10"].append(r10)
        cat_metrics[category]["mrr"].append(mrr_val)
        cat_metrics[category]["ndcg@10"].append(ndcg_val)
        if first_rank is not None:
            cat_metrics[category]["ranks"].append(first_rank)
        
        # Store detailed per-query info
        query_result = {
            "query": query_text,
            "category": category,
            "formulation": entry.get("formulation", "unknown"),
            "relevant_ids": list(relevant),
            "precision@1": p1,
            "precision@3": p3,
            "precision@5": p5,
            "precision@10": p10,
            "recall@10": r10,
            "mrr": mrr_val,
            "ndcg@10": ndcg_val,
            "first_relevant_rank": first_rank,
            "latency_ms": latency,
            "retrieved": [
                {
                    "entity_id": r.entity_id,
                    "name": r.name,
                    "score": float(r.score),
                    "rrf_score": float(r.rrf_score) if r.rrf_score else None,
                    "rank": r.rank,
                }
                for r in retrieved[:20]
            ],
        }
        per_query_results.append(query_result)
        
        if (i+1) % 200 == 0:
            print(f"  Processed {i+1}/{len(queries)}")
    
    # Aggregate
    summary = {
        "tag": tag,
        "num_queries": len(per_query_results),
        "total_attempted": len(queries),
        "precision@1": safe_mean(all_metrics["p@1"]),
        "precision@3": safe_mean(all_metrics["p@3"]),
        "precision@5": safe_mean(all_metrics["p@5"]),
        "precision@10": safe_mean(all_metrics["p@10"]),
        "recall@10": safe_mean(all_metrics["r@10"]),
        "mrr": safe_mean(all_metrics["mrr"]),
        "ndcg@10": safe_mean(all_metrics["ndcg@10"]),
        "avg_latency_ms": safe_mean(all_metrics["latency_ms"]),
        "p95_latency_ms": percentile(all_metrics["latency_ms"], 95),
        "p99_latency_ms": percentile(all_metrics["latency_ms"], 99),
        "avg_rank": safe_mean(all_metrics["ranks"]),
        "median_rank": median(all_metrics["ranks"]),
        "worst_rank": max(all_metrics["ranks"]) if all_metrics["ranks"] else None,
        "unique_assessments_retrieved": len(coverage),
        "total_assessments": 377,
        "coverage_pct": round(len(coverage) / 377 * 100, 1),
    }
    
    cat_summary = {}
    for cat, m in sorted(cat_metrics.items()):
        cat_summary[cat] = {
            "count": m["count"],
            "precision@1": safe_mean(m["p@1"]),
            "precision@3": safe_mean(m["p@3"]),
            "precision@5": safe_mean(m["p@5"]),
            "precision@10": safe_mean(m["p@10"]),
            "recall@10": safe_mean(m["r@10"]),
            "mrr": safe_mean(m["mrr"]),
            "ndcg@10": safe_mean(m["ndcg@10"]),
            "avg_rank": safe_mean(m["ranks"]),
            "median_rank": median(m["ranks"]),
            "worst_rank": max(m["ranks"]) if m["ranks"] else None,
        }
    
    return {"summary": summary, "cat_summary": cat_summary, "results": per_query_results}

def safe_mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0

def percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    sorted_vals = sorted(vals)
    idx = int(len(sorted_vals) * p / 100)
    return sorted_vals[min(idx, len(sorted_vals)-1)]

def median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2
    return sorted_vals[n//2]

# --- Main ---
if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("  COMPREHENSIVE RETRIEVAL AUDIT")
    print("=" * 60)
    
    # Initialize
    qb = QueryBuilder()
    retriever = HybridRetriever()
    retriever.initialize()
    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="audit",
        confidence="HIGH",
    )
    
    benchmarks = [
        ("Full Catalog Coverage", "benchmark/full_coverage_benchmark.json"),
        ("Unseen Stress Test", "benchmark/stress_benchmark.json"),
    ]
    
    all_results = {}
    
    for tag, path in benchmarks:
        if not Path(path).exists():
            print(f"\n  SKIP: {path} not found")
            continue
        
        print(f"\n{'='*60}")
        print(f"  BENCHMARK: {tag}")
        print(f"{'='*60}")
        
        queries = load_benchmark(path)
        print(f"  Loaded {len(queries)} queries")
        
        results = run_benchmark(queries, retriever, qb, decision, tag)
        all_results[tag] = results
        
        s = results["summary"]
        print(f"\n  RESULTS ({tag}):")
        print(f"  Queries run: {s['num_queries']}/{s['total_attempted']}")
        print(f"  precision@1:  {s['precision@1']:.4f}")
        print(f"  precision@3:  {s['precision@3']:.4f}")
        print(f"  precision@5:  {s['precision@5']:.4f}")
        print(f"  precision@10: {s['precision@10']:.4f}")
        print(f"  recall@10:    {s['recall@10']:.4f}")
        print(f"  mrr:          {s['mrr']:.4f}")
        print(f"  ndcg@10:      {s['ndcg@10']:.4f}")
        print(f"  avg_rank:     {s['avg_rank']:.2f}")
        print(f"  median_rank:  {s['median_rank']:.2f}")
        print(f"  worst_rank:   {s['worst_rank']}")
        print(f"  coverage:     {s['coverage_pct']:.1f}% ({s['unique_assessments_retrieved']}/{s['total_assessments']})")
        print(f"  latency:      {s['avg_latency_ms']:.1f}ms (p95: {s['p95_latency_ms']:.1f}ms)")
        
        # Save
        safe_tag = tag.lower().replace(' ', '_')
        out_path = f"benchmark/audit_{safe_tag}.json"
        with open(out_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  Saved to {out_path}")
    
    # --- Phase 3: False positive analysis ---
    print(f"\n{'='*60}")
    print("  PHASE 3: FALSE POSITIVE ANALYSIS")
    print(f"{'='*60}")
    
    # Load catalog
    with open('catalog/catalog.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    catalog_map = {r['entity_id']: r for r in catalog}
    
    # For each benchmark, analyze false positives
    for tag_key in all_results:
        results = all_results[tag_key]
        tag_short = tag_key[:20]
        total_fps = 0
        total_retrieved = 0
        
        for qr in results["results"]:
            relevant = set(qr["relevant_ids"])
            for r in qr["retrieved"][:10]:
                total_retrieved += 1
                if r["entity_id"] not in relevant:
                    total_fps += 1
        
        fp_rate = total_fps / total_retrieved if total_retrieved > 0 else 0
        print(f"  {tag_short}: FP rate = {fp_rate:.4f} ({total_fps}/{total_retrieved})")
    
    # --- Per-assessment coverage analysis ---
    print(f"\n{'='*60}")
    print("  PER-ASSESSMENT COVERAGE")
    print(f"{'='*60}")
    
    assessment_retrieved = {}
    for r in catalog:
        aid = r['entity_id']
        assessment_retrieved[aid] = {
            "name": r['name'],
            "retrieved_count": 0,
            "best_rank": None,
            "worst_rank": None,
            "avg_rank": [],
            "queries_attempted": 0,
        }
    
    # Use full coverage benchmark for per-assessment analysis
    fc_key = "Full Catalog Coverage"
    if fc_key in all_results:
        for qr in all_results[fc_key]["results"]:
            relevant = set(qr["relevant_ids"])
            for rid in relevant:
                if rid in assessment_retrieved:
                    assessment_retrieved[rid]["queries_attempted"] += 1
            for r in qr["retrieved"]:
                if r["entity_id"] in assessment_retrieved:
                    ar = assessment_retrieved[r["entity_id"]]
                    ar["retrieved_count"] += 1
                    if ar["best_rank"] is None or r["rank"] < ar["best_rank"]:
                        ar["best_rank"] = r["rank"]
                    if ar["worst_rank"] is None or r["rank"] > ar["worst_rank"]:
                        ar["worst_rank"] = r["rank"]
                    if r["entity_id"] in set(qr["relevant_ids"]):
                        ar["avg_rank"].append(r["rank"] if r["rank"] else 20)
        
        # Find never-retrieved assessments
        never_retrieved = []
        for aid, ar in assessment_retrieved.items():
            if ar["retrieved_count"] == 0:
                never_retrieved.append(ar["name"])
        
        print(f"  Never retrieved: {len(never_retrieved)}/{len(catalog)}")
        for n in never_retrieved[:20]:
            print(f"    - {n}")
        if len(never_retrieved) > 20:
            print(f"    ... and {len(never_retrieved)-20} more")
        
        # Finds assessments retrieved but never as relevant
        never_relevant = []
        for aid, ar in assessment_retrieved.items():
            if ar["retrieved_count"] > 0 and ar["queries_attempted"] > 0 and not ar["avg_rank"]:
                never_relevant.append(ar["name"])
        
        print(f"\n  Retrieved but never relevant for any query: {len(never_relevant)}/{len(catalog)}")
        for n in never_relevant[:10]:
            print(f"    - {n}")
    
    print(f"\n{'='*60}")
    print("  AUDIT COMPLETE")
    print(f"{'='*60}")
