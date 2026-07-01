"""Latency benchmark: measures end-to-end and per-stage pipeline timings."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable

from evaluation.metrics import latency_stats

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    stage: str
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def stats(self) -> dict:
        return latency_stats(self.latencies_ms)

    def to_dict(self) -> dict:
        return {"stage": self.stage, **self.stats}


@dataclass
class BenchmarkReport:
    results: list[BenchmarkResult] = field(default_factory=list)
    num_runs: int = 0

    def to_dict(self) -> dict:
        return {
            "num_runs": self.num_runs,
            "stages": {r.stage: r.stats for r in self.results},
        }


class Benchmark:
    """Measures latency for named pipeline stages across multiple runs."""

    def __init__(self) -> None:
        self._stages: dict[str, list[float]] = {}

    def measure(self, stage: str, fn: Callable, *args, **kwargs):
        """Run fn(*args, **kwargs), record elapsed ms under stage, return result."""
        start = perf_counter()
        result = fn(*args, **kwargs)
        elapsed_ms = (perf_counter() - start) * 1000
        self._stages.setdefault(stage, []).append(elapsed_ms)
        return result

    def report(self) -> BenchmarkReport:
        results = [
            BenchmarkResult(stage=stage, latencies_ms=lats)
            for stage, lats in self._stages.items()
        ]
        num_runs = max((len(r.latencies_ms) for r in results), default=0)
        report = BenchmarkReport(results=results, num_runs=num_runs)
        for r in results:
            s = r.stats
            logger.info(
                "Stage %-30s avg=%6.1f ms  p95=%6.1f ms  p99=%6.1f ms",
                r.stage,
                s["avg"],
                s["p95"],
                s["p99"],
            )
        return report


def run_pipeline_benchmark(
    pipeline_fn: Callable[[list[dict]], dict],
    conversations: list[list[dict]],
    num_runs: int = 3,
) -> BenchmarkReport:
    """
    Benchmark a pipeline function end-to-end.

    pipeline_fn: callable that accepts a conversation list and returns a timing dict
                 with keys like 'retrieval_ms', 'generation_ms', etc.
    conversations: list of conversation inputs to run.
    num_runs: number of repeats to stabilize measurements.
    """
    bench = Benchmark()
    for _ in range(num_runs):
        for conv in conversations:
            result = bench.measure("end_to_end", pipeline_fn, conv)
            # If the pipeline returns per-stage timings, record them
            if isinstance(result, dict):
                for stage_key, ms in result.items():
                    if stage_key.endswith("_ms") and isinstance(ms, (int, float)):
                        stage_name = stage_key.replace("_ms", "")
                        bench._stages.setdefault(stage_name, []).append(float(ms))

    return bench.report()
