"""CLI: Test the Response Validator (Module 18).

Usage
-----
  .venv\\Scripts\\python.exe scripts/test_validator.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.generation_models import LLMGenerationResult
from agent.validator import ResponseValidator, InvalidGenerationResult

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the Response Validator (Module 18).",
    )
    args = parser.parse_args()

    # Synthetic LLM Generation Result
    # Assumes "Verify - G+ General Ability" exists in the real catalog
    # And "Hallucinated Test" does not
    result = LLMGenerationResult(
        reply="Here are the recommended tests.",
        recommended_names=[
            "Verify - G+ General Ability",
            "Hallucinated Test",
            "verify - g+ general ability", # duplicate with different casing
        ],
        end_of_conversation=False,
        provider="mock",
        model="mock",
        latency_ms=100.0,
        tokens_prompt=50,
        tokens_completion=20,
        tokens_total=70,
        finish_reason="stop"
    )

    validator = ResponseValidator()

    started = perf_counter()
    try:
        validated = validator.validate(result)
    except InvalidGenerationResult as exc:
        print(f"[ERROR] Validation failed critically: {exc}", file=sys.stderr)
        sys.exit(1)
        
    elapsed_ms = (perf_counter() - started) * 1000

    print("\n" + "=" * 60)
    print("  VALIDATED GENERATION RESULT")
    print("=" * 60)
    print(f"Validation Passed : {validated.validation_passed}")
    if validated.validation_errors:
        print(f"Validation Errors : {validated.validation_errors}")
    print(f"Latency           : {elapsed_ms:.2f} ms")
    print("-" * 60)
    print(f"Reply             : {validated.reply}")
    print(f"Validated Names   : {validated.validated_names}")
    print(f"Invalid Names     : {validated.invalid_names}")
    print(f"End of Convo      : {validated.end_of_conversation}")
    print("=" * 60)
    print("\nFull JSON:")
    print(validated.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
