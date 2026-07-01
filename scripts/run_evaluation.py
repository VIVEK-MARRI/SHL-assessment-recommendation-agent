"""CLI: Run the SHL Evaluation Harness.

Usage
-----
  .venv\\Scripts\\python.exe scripts/run_evaluation.py --all
  .venv\\Scripts\\python.exe scripts/run_evaluation.py --retrieval --routing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import latency_stats
from evaluation.report_generator import generate_json_report, generate_markdown_report, print_summary


def _stub_retrieval_fn(query: str) -> list[str]:
    """Stub retrieval: returns empty list. Replace with live retriever for real eval."""
    return []


def _stub_route_fn(conversation: list[dict]) -> str:
    """Stub router: returns RECOMMEND always. Replace with live router for real eval."""
    return "RECOMMEND"


def _stub_extract_fn(conversation: list[dict]) -> dict:
    """Stub extractor: returns empty state. Replace with live extractor for real eval."""
    return {
        "intent": "recommend",
        "scope_flag": "recommend",
        "job_levels": [],
        "languages": [],
        "mentioned_assessment_names": [],
        "is_comparison_request": False,
        "end_of_conversation": False,
    }


def _stub_recommend_fn(conversation: list[dict]) -> list[str]:
    """Stub recommender: returns empty list. Replace with live pipeline for real eval."""
    return []


def run_retrieval() -> dict:
    from evaluation.retrieval_evaluator import RetrievalEvaluator

    ev = RetrievalEvaluator()
    metrics = ev.evaluate(_stub_retrieval_fn)
    return metrics.to_dict()


def run_routing() -> dict:
    from evaluation.router_evaluator import RouterEvaluator

    ev = RouterEvaluator()
    metrics = ev.evaluate(_stub_route_fn)
    return metrics.to_dict()


def run_state() -> dict:
    from evaluation.state_evaluator import StateEvaluator

    ev = StateEvaluator()
    metrics = ev.evaluate(_stub_extract_fn)
    return metrics.to_dict()


def run_recommendation() -> dict:
    from evaluation.recommendation_evaluator import RecommendationEvaluator

    ev = RecommendationEvaluator()
    metrics = ev.evaluate(_stub_recommend_fn)
    return metrics.to_dict()


def run_benchmark() -> dict:
    from evaluation.benchmark import Benchmark
    import time

    bench = Benchmark()

    def fake_e2e(conversation):
        time.sleep(0.01)
        return {"retrieval_ms": 8.0, "generation_ms": 50.0, "validation_ms": 1.0}

    for _ in range(5):
        bench.measure("end_to_end", fake_e2e, [{"role": "user", "content": "test"}])

    report = bench.report()
    return report.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the SHL Assessment Agent Evaluation Harness."
    )
    parser.add_argument("--retrieval", action="store_true", help="Run retrieval evaluation.")
    parser.add_argument("--routing", action="store_true", help="Run routing evaluation.")
    parser.add_argument("--state", action="store_true", help="Run state extraction evaluation.")
    parser.add_argument("--recommendation", action="store_true", help="Run recommendation evaluation.")
    parser.add_argument("--benchmark", action="store_true", help="Run latency benchmark.")
    parser.add_argument("--all", action="store_true", help="Run all evaluations.")
    args = parser.parse_args()

    run_all = args.all or not any(
        [args.retrieval, args.routing, args.state, args.recommendation, args.benchmark]
    )

    results = {}

    if run_all or args.retrieval:
        print("Running retrieval evaluation …")
        results["retrieval"] = run_retrieval()

    if run_all or args.routing:
        print("Running routing evaluation …")
        results["routing"] = run_routing()

    if run_all or args.state:
        print("Running state extraction evaluation …")
        results["state_extraction"] = run_state()

    if run_all or args.recommendation:
        print("Running recommendation evaluation …")
        results["recommendation"] = run_recommendation()

    if run_all or args.benchmark:
        print("Running benchmark …")
        results["benchmark"] = run_benchmark()

    print_summary(results)

    json_path = generate_json_report(results, name="evaluation")
    md_path = generate_markdown_report(results, name="evaluation")
    print(f"Reports saved:\n  JSON: {json_path}\n  MD:   {md_path}")


if __name__ == "__main__":
    main()
