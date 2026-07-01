"""Manual CLI for conversation state extraction.

Usage:
    .venv\\Scripts\\python.exe scripts\\test_state_extraction.py conversation.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.state_extraction import StateExtractor  # noqa: E402


def main() -> int:
    """Extract and print ConversationState for a JSON conversation file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if len(sys.argv) != 2:
        print("Usage: scripts/test_state_extraction.py conversation.json")
        return 2

    input_path = Path(sys.argv[1])
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read conversation JSON: {exc}")
        return 1

    messages = (
        payload["messages"]
        if isinstance(payload, dict) and "messages" in payload
        else payload
    )
    started_at = perf_counter()
    state = StateExtractor().extract(messages)
    elapsed_ms = (perf_counter() - started_at) * 1000

    print(json.dumps(state.model_dump(), indent=2, sort_keys=True))
    print(f"Execution time: {elapsed_ms:.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
