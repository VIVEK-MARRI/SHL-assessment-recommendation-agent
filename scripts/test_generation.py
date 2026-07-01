"""CLI: Test the LLM Response Generation (Module 17).

Usage
-----
  .venv\\Scripts\\python.exe scripts/test_generation.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompt_models import GroundingAssessment, PromptMetadata, PromptPackage
from agent.routing_models import RouteType
from agent.generation import ResponseGenerator
from agent.generation_client import GenerationError

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the LLM Response Generation (Module 17).",
    )
    args = parser.parse_args()

    # Synthetic PromptPackage
    package = PromptPackage(
        system_prompt="You are an SHL consultant. Output valid JSON.",
        user_prompt="I need a Python test.",
        route=RouteType.RECOMMEND,
        grounding_assessments=[
            GroundingAssessment(
                name="Python Knowledge Assessment",
                description="Tests advanced Python concepts.",
                duration="30 min",
                job_levels=["Senior"],
                languages=["English"],
                remote=True,
                adaptive=False,
                test_type=["Knowledge & Skills"],
                link="http://example.com/python"
            )
        ],
        metadata=PromptMetadata(
            prompt_version="1.0",
            route=RouteType.RECOMMEND,
            assessment_count=1,
            conversation_turns=1
        )
    )

    generator = ResponseGenerator()

    started = perf_counter()
    try:
        result = generator.generate(package)
    except GenerationError as exc:
        print(f"[ERROR] Generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
        
    elapsed_ms = (perf_counter() - started) * 1000

    print("\n" + "=" * 60)
    print("  LLM GENERATION RESULT")
    print("=" * 60)
    print(f"Provider        : {result.provider}")
    print(f"Model           : {result.model}")
    print(f"Finish Reason   : {result.finish_reason}")
    print(f"Latency         : {result.latency_ms:.2f} ms")
    print(f"Prompt Tokens   : {result.tokens_prompt}")
    print(f"Completion Toks : {result.tokens_completion}")
    print(f"Total Tokens    : {result.tokens_total}")
    print("-" * 60)
    print(f"Reply           : {result.reply}")
    print(f"Recommended     : {result.recommended_names}")
    print(f"End of Convo    : {result.end_of_conversation}")
    print("=" * 60)
    print("\nFull JSON:")
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
