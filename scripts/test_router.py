import argparse
import json
import sys
import logging
from pathlib import Path
from pydantic import ValidationError

sys.path.append(str(Path(__file__).parent.parent))

from agent.router import RuleBasedRouter
from agent.conversation_models import ConversationState

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def main():
    parser = argparse.ArgumentParser(description="Test the Rule-Based Router.")
    parser.add_argument(
        "--state",
        type=str,
        help="JSON string representing the ConversationState. If not provided, reads from stdin."
    )
    parser.add_argument(
        "--prev-state",
        type=str,
        help="Optional JSON string representing the previous ConversationState for testing REFINE."
    )
    
    args = parser.parse_args()
    
    state_json = args.state
    if not state_json:
        if not sys.stdin.isatty():
            state_json = sys.stdin.read()
        else:
            parser.error("Must provide --state or pipe JSON to stdin")
            
    try:
        state_dict = json.loads(state_json)
        state = ConversationState.model_validate(state_dict)
    except json.JSONDecodeError as e:
        print(f"Error parsing state JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Invalid ConversationState: {e}", file=sys.stderr)
        sys.exit(1)
        
    previous_state = None
    if args.prev_state:
        try:
            prev_dict = json.loads(args.prev_state)
            previous_state = ConversationState.model_validate(prev_dict)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error parsing previous state JSON: {e}", file=sys.stderr)
            sys.exit(1)

    router = RuleBasedRouter()
    
    try:
        decision = router.route(state, previous_state)
        print(f"Route: {decision.route.value}")
        print(f"Next Module: {decision.next_module}")
        print(f"Confidence: {decision.confidence}")
        print(f"Reason: {decision.reason}")
        print("\nFull JSON:")
        print(decision.model_dump_json(indent=2))
    except Exception as e:
        print(f"Routing failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
