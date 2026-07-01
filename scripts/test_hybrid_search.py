"""Manual verification CLI for hybrid retrieval.

Usage:
    py scripts/test_hybrid_search.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from statistics import mean
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from retrieval.hybrid_retriever import HybridRetriever  # noqa: E402


def main() -> int:
    """Run example hybrid searches against the production retrievers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    retriever = HybridRetriever()
    retriever.initialize()

    queries = [
        "Java Developer",
        "Python Backend",
        "Sales Manager",
        "Leadership Assessment",
        "Customer Service",
    ]
    latencies: list[float] = []
    overlaps: list[int] = []

    for query in queries:
        started_at = perf_counter()
        result = retriever.search(query, top_k=5)
        elapsed_ms = (perf_counter() - started_at) * 1000
        latencies.append(elapsed_ms)
        overlaps.append(
            sum(
                1
                for item in result.results
                if item.embedding_rank is not None and item.bm25_rank is not None
            )
        )

        print(f"\nQuery: {query}")
        print(f"Confidence: {result.confidence} | {result.reason}")
        print(f"Execution time: {elapsed_ms:.2f} ms")
        for item in result.results[:5]:
            print(
                f"{item.rank}. {item.name} | "
                f"embedding_rank={item.embedding_rank} | "
                f"bm25_rank={item.bm25_rank} | "
                f"rrf={item.rrf_score:.6f}"
            )

        if len({item.entity_id for item in result.results}) != len(result.results):
            logger.error("Duplicate assessments returned for query: %s", query)
            return 1
        scores = [item.rrf_score for item in result.results]
        if scores != sorted(scores, reverse=True):
            logger.error("RRF scores are not monotonically decreasing for query: %s", query)
            return 1

    health = retriever.health()
    embedding_latency = _format_latency(health.embedding_latency_ms)
    bm25_latency = _format_latency(health.bm25_latency_ms)
    hybrid_latency = _format_latency(health.average_latency_ms or mean(latencies))
    print(f"\nEmbedding latency: {embedding_latency}")
    print(f"BM25 latency: {bm25_latency}")
    print(f"Hybrid latency: {hybrid_latency}")
    print(f"Average overlap: {mean(overlaps):.2f}")
    return 0


def _format_latency(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value:.2f} ms"


if __name__ == "__main__":
    raise SystemExit(main())
