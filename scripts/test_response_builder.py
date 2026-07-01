"""CLI: Test the Response Builder (Module 19).

Usage
-----
  .venv\\Scripts\\python.exe scripts/test_response_builder.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.response_builder import ResponseBuilder, ResponseBuilderError
from agent.routing_models import RouteType, RoutingDecision
from agent.validator_models import ValidatedGenerationResult


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Response Builder (Module 19).",
    )
    args = parser.parse_args()

    # Synthetic validated result
    validated = ValidatedGenerationResult(
        reply="Based on your requirements, I recommend the following SHL assessments.",
        validated_names=[
            ".NET Framework 4.5",  # Real name from catalog
        ],
        invalid_names=[],
        end_of_conversation=False,
        validation_passed=True,
        validation_errors=[],
    )

    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="test",
        confidence="HIGH",
    )

    builder = ResponseBuilder()

    started = perf_counter()
    try:
        response = builder.build(validated=validated, decision=decision)
    except ResponseBuilderError as exc:
        print(f"[ERROR] ResponseBuilder failed: {exc}", file=sys.stderr)
        sys.exit(1)

    elapsed_ms = (perf_counter() - started) * 1000

    print("\n" + "=" * 60)
    print("  CHAT RESPONSE")
    print("=" * 60)
    print(f"Route           : {decision.route.value}")
    print(f"Latency         : {elapsed_ms:.2f} ms")
    print(f"Reply           : {response.reply}")
    print(f"Recommendations : {len(response.recommendations) if response.recommendations else 'null'}")
    if response.recommendations:
        for rec in response.recommendations:
            print(f"  - {rec.name} | {rec.test_type} | {rec.url}")
    print("=" * 60)
    print("\nFull JSON:")
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
