"""CLI: Test the Prompt Builder (Module 16).

Usage
-----
  .venv\\Scripts\\python.exe scripts/test_prompt_builder.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.conversation_models import ConversationMessage, ConversationState
from agent.prompt_builder import PromptBuilder, PromptBuilderError
from agent.routing_models import RouteType, RoutingDecision
from retrieval.retrieval_models import RetrievedAssessment

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Prompt Builder (Module 16).",
    )
    args = parser.parse_args()

    # Synthetic inputs
    conversation = [
        ConversationMessage(role="user", content="I am looking for a senior python developer test."),
    ]
    state = ConversationState(role="Python Developer", seniority="Senior")
    decision = RoutingDecision(
        route=RouteType.RECOMMEND,
        next_module="query_builder",
        reason="ok",
        confidence="HIGH",
        query_required=True,
        recommendation_required=True,
    )
    
    retrieved = [
        RetrievedAssessment(
            entity_id="1234",
            name="Python Programming Advanced",
            url="http://example.com/python-adv",
            score=0.9,
            rank=1,
            test_type="Knowledge & Skills",
            duration="30 min",
            job_levels=["Senior"],
            languages=["English"],
            remote=True,
            adaptive=False,
            keys=["Knowledge"],
        )
    ]

    builder = PromptBuilder()

    started = perf_counter()
    try:
        package = builder.build(
            conversation=conversation,
            state=state,
            decision=decision,
            retrieved_assessments=retrieved
        )
    except PromptBuilderError as exc:
        print(f"[ERROR] PromptBuilder failed: {exc}", file=sys.stderr)
        sys.exit(1)
        
    elapsed_ms = (perf_counter() - started) * 1000

    print("\n" + "=" * 60)
    print("  PROMPT PACKAGE")
    print("=" * 60)
    print(f"Route           : {package.route.value}")
    print(f"System Prompt   : {package.system_prompt[:60]}...")
    print(f"User Prompt     : {package.user_prompt[:60]}...")
    print(f"Grounding Items : {len(package.grounding_assessments)}")
    print()
    print("Metadata")
    print(f"  Version     : {package.metadata.prompt_version}")
    print(f"  Turns       : {package.metadata.conversation_turns}")
    print(f"  Generated At: {package.metadata.generated_at}")
    print()
    print(f"Latency         : {elapsed_ms:.2f} ms")
    print("=" * 60)
    print("\nFull JSON:")
    print(package.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
