"""Manual verification CLI for semantic embedding retrieval.

Usage:
    py scripts/test_embedding_search.py
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

from retrieval.embedding_retriever import EmbeddingRetriever  # noqa: E402


def main() -> int:
    """Run several example semantic searches against the persisted index."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    retriever = EmbeddingRetriever()
    retriever.initialize()
    health = retriever.health()

    queries = [
        "Java developer coding test",
        "sales manager personality assessment",
        "graduate numerical reasoning",
        "cyber security knowledge assessment",
    ]

    latencies: list[float] = []
    print(
        "Indexed assessments: "
        f"{health.number_of_indexed_assessments} | "
        f"Embedding dimension: {health.embedding_dimension} | "
        f"Model: {health.model_name} | "
        f"Metadata loaded: {health.metadata_loaded} | "
        f"Catalog SHA: {health.catalog_sha}"
    )
    for query in queries:
        started_at = perf_counter()
        results = retriever.search(query, top_k=5)
        elapsed_ms = (perf_counter() - started_at) * 1000
        latencies.append(elapsed_ms)

        print(f"\nQuery: {query}")
        print(f"Execution time: {elapsed_ms:.2f} ms")
        for result in results[:5]:
            print(f"{result.rank}. {result.name} | score={result.score:.4f} | {result.url}")

        scores = [result.score for result in results]
        if scores != sorted(scores, reverse=True):
            logger.error("Scores are not monotonically decreasing for query: %s", query)
            return 1
        if len({result.entity_id for result in results}) != len(results):
            logger.error("Duplicate assessments returned for query: %s", query)
            return 1

    final_health = retriever.health()
    print(f"\nAverage query latency: {mean(latencies):.2f} ms")
    print(f"Retriever health average latency: {final_health.average_query_latency_ms:.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
