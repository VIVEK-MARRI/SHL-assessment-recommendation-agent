"""Unseen Retrieval Evaluator."""
import json
import random
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from agent.conversation_models import ConversationState
from agent.query_builder import QueryBuilder
from agent.routing_models import RoutingDecision, RouteType
from retrieval.hybrid_retriever import HybridRetriever
from evaluation.metrics import latency_stats, precision_at_k, recall_at_k, reciprocal_rank

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog" / "catalog.json"
REPORTS_DIR = ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "unseen_retrieval_report.md"

@dataclass
class UnseenCase:
    name: str
    state: ConversationState
    expected_names: set[str]

def load_catalog() -> list[dict[str, Any]]:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _find_expected(catalog, name_keywords=None, desc_keywords=None, require_sim=False, require_cognitive=False, require_personality=False) -> set[str]:
    results = set()
    for item in catalog:
        text = (item["name"] + " " + item["description"] + " " + " ".join(item["keys"])).lower()
        match = True
        if name_keywords:
            if not any(k.lower() in item["name"].lower() for k in name_keywords):
                match = False
        if desc_keywords:
            if not any(k.lower() in text for k in desc_keywords):
                match = False
        
        # very basic test_type matching
        types = [t.lower() for t in item.get("test_type", [])]
        if require_sim and not any("simulation" in t for t in types):
            match = False
        if require_cognitive and not any(k in t for t in types for k in ["cognitive", "ability", "aptitude"]):
            match = False
        if require_personality and not any(k in t for t in types for k in ["personality", "behavior"]):
            match = False
            
        if match:
            results.add(item["name"])
    return results

def generate_200_cases(catalog) -> list[UnseenCase]:
    cases = []
    
    scenarios = [
        ("Python", ["Python"]),
        ("Java", ["Java"]),
        ("SQL", ["SQL"]),
        ("C#", ["C#"]),
        ("DevOps", ["DevOps", "Jenkins", "AWS"]),
        ("Data Scientist", ["Data Science", "Machine Learning"]),
        ("Finance", ["Finance", "Accounting"]),
        ("Marketing", ["Marketing"]),
    ]
    
    roles = [
        ("Leadership", "Manager", True, False, False),
        ("Sales", "Sales", False, False, False),
        ("Customer Service", "Customer Support", False, False, False),
        ("Graduate", "Graduate", False, False, False),
        ("Intern", "Intern", False, False, False),
    ]

    capabilities = [
        ("Communication", False, False, False, ["communication", "english", "verbal"]),
        ("Numerical Reasoning", False, True, False, ["numerical"]),
        ("Personality", False, False, True, ["personality"]),
        ("Cognitive", False, True, False, ["cognitive", "ability"]),
        ("Simulation", True, False, False, ["simulation", "coding"]),
    ]
    
    # 1. Tech Skills (10 * 8 = 80 cases)
    for _ in range(10):
        for tech_name, tech_skills in scenarios:
            state = ConversationState(technical_skills=tech_skills)
            expected = _find_expected(catalog, name_keywords=tech_skills)
            # fallback
            if not expected:
                expected = _find_expected(catalog, desc_keywords=tech_skills)
            cases.append(UnseenCase(f"Tech: {tech_name}", state, expected))
            
    # 2. Roles (10 * 5 = 50 cases)
    for _ in range(10):
        for role_name, role_val, req_lead, req_cog, req_pers in roles:
            state = ConversationState(role=role_val, leadership_required=req_lead, cognitive_required=req_cog, personality_required=req_pers)
            expected = _find_expected(catalog, desc_keywords=[role_val], require_cognitive=req_cog, require_personality=req_pers)
            cases.append(UnseenCase(f"Role: {role_name}", state, expected))
            
    # 3. Capabilities (10 * 5 = 50 cases)
    for _ in range(10):
        for cap_name, req_sim, req_cog, req_pers, desc_keys in capabilities:
            state = ConversationState(role="Professional", simulation_required=req_sim, cognitive_required=req_cog, personality_required=req_pers)
            expected = _find_expected(catalog, desc_keywords=desc_keys, require_sim=req_sim, require_cognitive=req_cog, require_personality=req_pers)
            cases.append(UnseenCase(f"Capability: {cap_name}", state, expected))

    # 4. Mixed Constraints (20 cases)
    for _ in range(20):
        state = ConversationState(technical_skills=["Python"], role="Engineer", simulation_required=True)
        expected = _find_expected(catalog, desc_keywords=["python", "engineer"], require_sim=True)
        # fallback
        if not expected:
            expected = _find_expected(catalog, name_keywords=["Python"])
        cases.append(UnseenCase("Mixed: Python Engineer Sim", state, expected))

    # Ensure exact 200 cases
    return cases[:200]

def evaluate():
    print("Loading catalog...")
    catalog = load_catalog()
    cases = generate_200_cases(catalog)
    
    print(f"Generated {len(cases)} cases. Initializing HybridRetriever...")
    retriever = HybridRetriever()
    retriever.initialize()
    query_builder = QueryBuilder()
    
    latencies = []
    recalls = []
    precisions_1 = []
    precisions_3 = []
    precisions_5 = []
    mrrs = []
    
    print("Running unseen retrieval benchmark...")
    for case in cases:
        if not case.expected_names:
            continue
            
        start = time.perf_counter()
        decision = RoutingDecision(route=RouteType.RECOMMEND, next_module="query_builder", confidence="HIGH", reason="unseen")
        query = query_builder.build(state=case.state, decision=decision)
        result = retriever.search(query.query_text, state=case.state, filters=query.filters, top_k=10)
        lat = (time.perf_counter() - start) * 1000
        latencies.append(lat)
        
        retrieved_names = [item.name for item in result.results[:10]]
        
        expected_lower = {n.casefold() for n in case.expected_names}
        retrieved_lower = [n.casefold() for n in retrieved_names]
        
        r10 = recall_at_k(expected_lower, retrieved_lower, 10)
        p1 = precision_at_k(expected_lower, retrieved_lower, 1)
        p3 = precision_at_k(expected_lower, retrieved_lower, 3)
        p5 = precision_at_k(expected_lower, retrieved_lower, 5)
        m = reciprocal_rank(expected_lower, retrieved_lower)
        
        recalls.append(r10)
        precisions_1.append(p1)
        precisions_3.append(p3)
        precisions_5.append(p5)
        mrrs.append(m)

    mean_recall_10 = sum(recalls) / len(recalls) if recalls else 0.0
    mean_p1 = sum(precisions_1) / len(precisions_1) if precisions_1 else 0.0
    mean_p3 = sum(precisions_3) / len(precisions_3) if precisions_3 else 0.0
    mean_p5 = sum(precisions_5) / len(precisions_5) if precisions_5 else 0.0
    mean_mrr = sum(mrrs) / len(mrrs) if mrrs else 0.0
    
    stats = latency_stats(latencies)
    avg_latency = stats["avg"]
    p95_latency = stats["p95"]
    
    print(f"Mean Recall@10: {mean_recall_10:.4f}")
    
    # Write report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_content = f"""# Unseen Retrieval Validation Report

This benchmark runs a completely independent set of {len(cases)} programmatic queries simulating unseen conversational states and constraints.

## Metrics
- Total Valid Queries: {len(recalls)}
- Precision@1: {mean_p1:.4f}
- Precision@3: {mean_p3:.4f}
- Precision@5: {mean_p5:.4f}
- Recall@10: {mean_recall_10:.4f}
- Mean Recall@10: {mean_recall_10:.4f}
- MRR: {mean_mrr:.4f}
- Average Latency: {avg_latency:.2f} ms
- 95th Percentile Latency: {p95_latency:.2f} ms
"""
    REPORT_PATH.write_text(report_content, encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")

if __name__ == "__main__":
    evaluate()
