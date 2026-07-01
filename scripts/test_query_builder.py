"""CLI: Test the Query Builder interactively.

Usage
-----
# Minimal recommend state
.venv\\Scripts\\python.exe scripts/test_query_builder.py \\
    --state '{"role":"Python Developer","technical_skills":["Django","Flask"]}' \\
    --decision '{"route":"RECOMMEND","next_module":"query_builder","reason":"ok","confidence":"HIGH","query_required":true,"recommendation_required":true}'

# With previous-state for REFINE (optional)
... --decision '{"route":"REFINE",...}'
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

from agent.conversation_models import ConversationState
from agent.query_builder import InvalidConversationState, InvalidRoutingDecision, QueryBuilder
from agent.routing_models import RoutingDecision

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")


def _load_json(raw: str, label: str) -> dict:  # type: ignore[type-arg]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Could not parse {label} JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Query Builder (Module 14).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--state", required=True, help="ConversationState JSON string")
    parser.add_argument("--decision", required=True, help="RoutingDecision JSON string")
    args = parser.parse_args()

    state_dict = _load_json(args.state, "ConversationState")
    decision_dict = _load_json(args.decision, "RoutingDecision")

    try:
        state = ConversationState.model_validate(state_dict)
    except ValidationError as exc:
        print(f"[ERROR] Invalid ConversationState:\n{exc}", file=sys.stderr)
        sys.exit(1)

    try:
        decision = RoutingDecision.model_validate(decision_dict)
    except ValidationError as exc:
        print(f"[ERROR] Invalid RoutingDecision:\n{exc}", file=sys.stderr)
        sys.exit(1)

    builder = QueryBuilder()
    started = perf_counter()

    try:
        query = builder.build(state, decision)
    except (InvalidConversationState, InvalidRoutingDecision) as exc:
        print(f"[ERROR] QueryBuilder failed: {exc}", file=sys.stderr)
        sys.exit(1)

    elapsed_ms = (perf_counter() - started) * 1000

    # --- Pretty output ------------------------------------------------------
    print("\n" + "=" * 60)
    print("  RETRIEVAL QUERY")
    print("=" * 60)
    print(f"Route           : {decision.route.value}")
    print(f"Next Module     : {decision.next_module}")
    print(f"Query Text      : {query.query_text}")
    print(f"Required Terms  : {query.required_terms}")
    print(f"Optional Terms  : {query.optional_terms}")
    print(f"Excluded Terms  : {query.excluded_terms}")
    print(f"Expansion Terms : {query.expansion_terms}")
    print()
    print("Filters")
    print(f"  Job Levels    : {query.filters.job_levels}")
    print(f"  Languages     : {query.filters.languages}")
    print(f"  Max Duration  : {query.filters.maximum_duration_minutes} min")
    print(f"  Test Types    : {query.filters.test_types}")
    print(f"  Remote Only   : {query.filters.remote_only}")
    print(f"  Adaptive Only : {query.filters.adaptive_only}")
    print()
    print(f"Latency         : {elapsed_ms:.2f} ms")
    print("=" * 60)
    print("\nFull JSON:")
    print(query.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
