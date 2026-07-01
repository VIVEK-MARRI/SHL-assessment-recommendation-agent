"""CLI: Test the Comparison Pipeline (Module 15).

Usage
-----
  .venv\\Scripts\\python.exe scripts/test_comparison.py \\
      --state '{"mentioned_assessment_names":["Python (New)","Agile Software Development"],"comparison_requested":true}'

  # Pipe JSON from stdin
  echo '{"mentioned_assessment_names":["OPQ User Report"]}' | \\
      .venv\\Scripts\\python.exe scripts/test_comparison.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from time import perf_counter

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.catalog_matcher import CatalogMatcher
from agent.comparison import ComparisonError, ComparisonPipeline, InvalidComparisonRequest
from agent.conversation_models import ConversationState
from agent.routing_models import RouteType, RoutingDecision

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")


def _parse_state(raw: str) -> ConversationState:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON for ConversationState: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        return ConversationState.model_validate(data)
    except ValidationError as exc:
        print(f"[ERROR] ConversationState validation failed:\n{exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Comparison Pipeline (Module 15).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--state",
        type=str,
        help="ConversationState JSON string. Reads from stdin if omitted.",
    )
    args = parser.parse_args()

    raw = args.state
    if not raw:
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
        else:
            parser.error("Provide --state or pipe JSON to stdin.")

    state = _parse_state(raw)

    # Build a synthetic COMPARE decision for the CLI
    decision = RoutingDecision(
        route=RouteType.COMPARE,
        next_module="comparison_pipeline",
        reason="CLI invocation",
        confidence="HIGH",
        query_required=True,
        comparison_required=True,
    )

    matcher = CatalogMatcher()
    pipeline = ComparisonPipeline(matcher=matcher)

    started = perf_counter()
    try:
        ctx = pipeline.run(state, decision)
    except (InvalidComparisonRequest, ComparisonError) as exc:
        print(f"[ERROR] Comparison failed: {exc}", file=sys.stderr)
        sys.exit(1)
    elapsed_ms = (perf_counter() - started) * 1000

    # --- Pretty output ---------------------------------------------------
    print("\n" + "=" * 60)
    print("  COMPARISON CONTEXT")
    print("=" * 60)
    print(f"Comparison Possible : {ctx.comparison_possible}")
    print(f"Reason              : {ctx.reason}")
    print(f"Matched ({len(ctx.matched_assessments)})")
    for a in ctx.matched_assessments:
        print(f"  • {a.name}")
        print(f"      ID       : {a.entity_id}")
        print(f"      Type     : {a.test_type}")
        print(f"      Duration : {a.duration}")
        print(f"      Levels   : {a.job_levels}")
        print(f"      Remote   : {a.remote}  Adaptive: {a.adaptive}")
        print(f"      URL      : {a.url}")
    if ctx.unmatched_names:
        print(f"Unmatched ({len(ctx.unmatched_names)})")
        for name in ctx.unmatched_names:
            print(f"  [X] {name}")
    print()
    print(f"Latency             : {elapsed_ms:.2f} ms")
    print("=" * 60)
    print("\nFull JSON:")
    print(ctx.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
