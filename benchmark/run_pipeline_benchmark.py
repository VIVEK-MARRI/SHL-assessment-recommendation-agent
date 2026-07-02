"""Full-pipeline benchmark — constructs ConversationState for each query and runs QueryBuilder + HybridRetriever."""
from __future__ import annotations
import json, logging, sys, time, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.WARNING)
import numpy as np

from agent.conversation_models import ConversationState
from agent.query_builder import QueryBuilder
from agent.query_models import QueryFilters
from agent.routing_models import RouteType, RoutingDecision
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.retrieval_models import RetrievedAssessment

# --- Metrics ---
def precision_at_k(relevant: set[str], retrieved, k: int) -> float:
    top = retrieved[:k]
    if not top: return 0.0
    hits = sum(1 for r in top if r.entity_id in relevant)
    return hits / k if relevant else 1.0

def recall_at_k(relevant: set[str], retrieved, k: int) -> float:
    if not relevant: return 1.0
    hits = sum(1 for r in retrieved[:k] if r.entity_id in relevant)
    return hits / len(relevant)

def mrr_fn(relevant: set[str], retrieved):
    for i, r in enumerate(retrieved, start=1):
        if r.entity_id in relevant: return 1.0 / i
    return 0.0

def ndcg_at_k(relevant: set[str], retrieved, k: int) -> float:
    k = min(k, len(retrieved))
    if k == 0: return 0.0
    dcg = 0.0
    for i in range(k):
        rel = 1.0 if retrieved[i].entity_id in relevant else 0.0
        dcg += (2**rel - 1) / np.log2(i + 2)
    ideal_rel = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_rel))
    if idcg == 0: return 0.0
    return dcg / idcg

# --- State builder ---
_SENIORITY_WORDS = {"graduate", "entry", "junior", "senior", "lead", "fresher", "new", "intern", "apprentice"}

def build_state(query: str, category: str) -> ConversationState:
    """Derive a ConversationState from query text and category."""
    q_lower = query.casefold()
    state = ConversationState()

    # Seniority detection
    for word in _SENIORITY_WORDS:
        if word in q_lower:
            if word == "new":
                if "new grad" in q_lower or "new graduate" in q_lower:
                    state.seniority = "graduate"
                else:
                    state.seniority = None
            else:
                state.seniority = word
            break

    # Role detection
    role_patterns = [
        (r"software\s+(?:engineer|developer)", "Software Engineer"),
        (r"backend\s+(?:developer|engineer)", "Backend Developer"),
        (r"frontend\s+(?:developer|engineer)", "Frontend Developer"),
        (r"data\s+scientist", "Data Scientist"),
        (r"(?:devops|site\s+reliability)\s+(?:engineer|developer)", "DevOps Engineer"),
        (r"(?:security|cyber)\s+(?:engineer|analyst)", "Security Engineer"),
        (r"(?:cloud|aws|azure)\s+(?:engineer|developer)", "Cloud Engineer"),
        (r"(?:machine\s+learning|ml|data)\s+(?:engineer|scientist)", "Data Scientist"),
        (r"(?:qa|test)\s+(?:engineer|developer)", "QA Engineer"),
        (r"(?:ios|android|mobile)\s+(?:developer|engineer)", "Mobile Developer"),
        (r"(python|java|sql)\s+(?:developer|engineer)", lambda m: f"{m.group(1).title()} Developer"),
        (r"(?:full.?stack|fullstack)\s+(?:developer|engineer)", "Full Stack Developer"),
        (r"(?:product|project|program)\s+manager", "Project Manager"),
        (r"(?:sales|account)\s+(?:manager|representative)", "Sales Manager"),
        (r"(?:customer\s+service|support)\s+(?:representative|manager)", "Customer Service Representative"),
        (r"(?:business\s+)?analyst", "Business Analyst"),
        (r"(?:hr|human\s+resources|recruitment|talent)\s+", "HR Manager"),
        (r"(?:marketing|brand|digital).*?manager", "Marketing Manager"),
    ]
    for pattern, role in role_patterns:
        match = re.search(pattern, q_lower)
        if match:
            state.role = role(match) if callable(role) else role
            break

    # Capabilities based on category
    if category == "cognitive":
        state.cognitive_required = True
    elif category == "personality":
        state.personality_required = True
    elif category == "simulation":
        state.simulation_required = True
    elif category == "leadership":
        state.leadership_required = True

    # Technical skills from query
    tech_patterns = [
        (r"\bpython\b", "Python"), (r"\bjava\b(?!script)", "Java"), (r"\bsql\b", "SQL"),
        (r"\bjavascript\b", "JavaScript"), (r"\btypescript\b", "TypeScript"),
        (r"\breact\b", "React"), (r"\bangular\b", "Angular"), (r"\bvue\b", "Vue"),
        (r"\bdocker\b", "Docker"), (r"\bkubernetes\b", "Kubernetes"),
        (r"\baws\b", "AWS"), (r"\bazure\b", "Azure"), (r"\bgcp\b", "GCP"),
        (r"\bsap\b", "SAP"), (r"\boracle\b", "Oracle"),
        (r"\bhtml\b", "HTML"), (r"\bcss\b", "CSS"),
        (r"\bnode\b", "Node.js"), (r"\bdjango\b", "Django"),
        (r"\bflask\b", "Flask"), (r"\bspring\b", "Spring"),
        (r"\bselenium\b", "Selenium"), (r"\bdotnet\b|\.net\b", ".NET"),
        (r"\bc\+\+\b", "C++"), (r"\bc#\b|csharp", "C#"),
        (r"\bgo\b", "Go"), (r"\brust\b", "Rust"),
        (r"\bruby\b", "Ruby"), (r"\bphp\b", "PHP"),
        (r"\bscala\b", "Scala"), (r"\br\b(?!programming)", "R"),
        (r"\bmachine learning\b|ml\b", "Machine Learning"),
        (r"\bai\b|artificial intelligence", "AI"),
        (r"\bswift\b", "Swift"), (r"\bkotlin\b", "Kotlin"),
        (r"\bflutter\b", "Flutter"), (r"\bterraform\b", "Terraform"),
        (r"\bansible\b", "Ansible"), (r"\bjenkins\b", "Jenkins"),
        (r"\bsalesforce\b", "Salesforce"),
    ]
    skills = []
    for pattern, name in tech_patterns:
        if re.search(pattern, q_lower):
            skills.append(name)
    state.technical_skills = skills

    return state

# --- Benchmark runner ---
def run_full_pipeline_benchmark(benchmark_path: Path, tag: str = "full_pipeline") -> dict:
    with open(benchmark_path, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"\n{'='*60}")
    print(f"  FULL PIPELINE BENCHMARK: {tag}  ({len(queries)} queries)")
    print(f"{'='*60}")

    qb = QueryBuilder()
    retriever = HybridRetriever()
    retriever.initialize()

    all_metrics = {"p@1":[],"p@3":[],"p@5":[],"p@10":[],"r@10":[],"mrr":[],"ndcg@10":[],"latency_ms":[],"coverage":set()}
    cat_metrics: dict = {}

    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="benchmark",
        confidence="HIGH",
    )

    for i, entry in enumerate(queries):
        query = entry["query"]
        relevant = set(entry["relevant_ids"])
        category = entry.get("category", "general")

        if category not in cat_metrics:
            cat_metrics[category] = {"p@1":[],"p@3":[],"p@5":[],"p@10":[],"r@10":[],"mrr":[],"ndcg@10":[],"count":0}
        cat_metrics[category]["count"] += 1

        state = build_state(query, category)

        # Build retrieval query
        try:
            retrieval_query = qb.build(state, decision)
        except Exception as e:
            print(f"  WARN: QueryBuilder failed for '{query}': {e}")
            continue

        # Retrieve (pass empty state to isolate QueryBuilder improvements from MetadataReranker effects)
        start = time.perf_counter()
        try:
            result = retriever.search(
                retrieval_query.query_text,
                state=ConversationState(),
                filters=QueryFilters(),
                top_k=20,
            )
            retrieved = result.results
        except Exception as e:
            print(f"  WARN: Search failed for '{query}': {e}")
            continue
        latency = (time.perf_counter() - start) * 1000
        all_metrics["latency_ms"].append(latency)
        all_metrics["coverage"].update(r.entity_id for r in retrieved)

        p1 = precision_at_k(relevant, retrieved, 1)
        p3 = precision_at_k(relevant, retrieved, 3)
        p5 = precision_at_k(relevant, retrieved, 5)
        p10 = precision_at_k(relevant, retrieved, 10)
        r10 = recall_at_k(relevant, retrieved, 10)
        mrr_val = mrr_fn(relevant, retrieved)
        ndcg_val = ndcg_at_k(relevant, retrieved, 10)

        for m, v in [("p@1",p1),("p@3",p3),("p@5",p5),("p@10",p10),("r@10",r10),("mrr",mrr_val),("ndcg@10",ndcg_val)]:
            all_metrics[m].append(v)
            cat_metrics[category][m].append(v)

        if (i+1)%50==0:
            print(f"  Processed {i+1}/{len(queries)}")

    summary = {
        "tag": tag,
        "num_queries": len(queries),
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
        "coverage_pct": round(len(all_metrics["coverage"])/377*100, 1),
    }

    cat_summary = {}
    for cat, m in sorted(cat_metrics.items()):
        if m["count"]>0:
            cat_summary[cat] = {
                "count": m["count"],
                "precision@1": float(np.mean(m["p@1"])),
                "precision@3": float(np.mean(m["p@3"])),
                "precision@5": float(np.mean(m["p@5"])),
                "recall@10": float(np.mean(m["r@10"])),
                "mrr": float(np.mean(m["mrr"])),
            }

    print(f"\n  RESULTS ({tag}):")
    print(f"  Queries: {summary['num_queries']}")
    for k in ["precision@1","precision@3","precision@5","precision@10","recall@10","mrr","ndcg@10"]:
        print(f"  {k}: {summary[k]:.4f}")
    print(f"  Avg Latency: {summary['avg_latency_ms']:.2f}ms  P95: {summary['p95_latency_ms']:.2f}ms")
    print(f"  Coverage: {summary['unique_assessments_retrieved']}/{summary['total_assessments']} ({summary['coverage_pct']}%)")

    return {"summary": summary, "cat_summary": cat_summary}

if __name__ == "__main__":
    benchmark_path = ROOT / "benchmark" / "retrieval_benchmark.json"
    results = run_full_pipeline_benchmark(benchmark_path, tag="improved")
    (ROOT / "benchmark" / "pipeline_improved.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to benchmark/pipeline_improved.json")
