"""Manual verification CLI for lexical BM25 retrieval.

Usage:
    py scripts/test_bm25_search.py
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

from retrieval.bm25_retriever import BM25Retriever  # noqa: E402


def main() -> int:
    """Run several example lexical searches against the persisted BM25 index."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    retriever = BM25Retriever()
    retriever.initialize()
    health = retriever.health()

    queries = [
        "Java developer coding test",
        "sales manager personality assessment",
        "graduate numerical reasoning",
        "C++ .NET developer",
    ]

    latencies: list[float] = []
    print(
        "Indexed documents: "
        f"{health.document_count} | "
        f"Tokenizer: {health.tokenizer_version} | "
        f"Catalog SHA: {health.catalog_sha256}"
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
