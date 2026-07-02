"""Part 3: Hard Evaluation - Code + Schema audit (no server needed)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.response_models import ChatResponse, Recommendation
from agent.conversation_models import ConversationMessage, ConversationState
from agent.router import RuleBasedRouter
from agent.routing_models import RouteType
from app.schemas import ChatRequest

catalog = json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))
cn = {i["name"].casefold() for i in catalog}
print(f"Catalog: {len(catalog)} assessments")

checks = []

# 1. ChatRequest schema
req = ChatRequest(messages=[ConversationMessage(role="user", content="test")])
assert len(req.messages) == 1
checks.append(("ChatRequest accepts valid messages", True))

# 2. ChatResponse schema
rec = Recommendation(name="Test", url="http://test.com", test_type=["Knowledge"])
resp = ChatResponse(reply="Reply", recommendations=[rec])
assert resp.reply == "Reply"
assert len(resp.recommendations) == 1
checks.append(("ChatResponse accepts reply + recommendations", True))

# 3. ChatResponse fields
props = set(ChatResponse.model_fields.keys())
expected = {"reply", "recommendations"}
checks.append((f"ChatResponse fields = {props}", props == expected))

# 4. No end_of_conversation in public API
checks.append(("end_of_conversation NOT in public schema", "end_of_conversation" not in props))

# 5. Catalog - all entries have name + url/link
missing = sum(1 for i in catalog if not i.get("name") or not (i.get("url") or i.get("link")))
checks.append(("All catalog entries have required fields", missing == 0))

# 6. Catalog - no duplicates
names = [i["name"].casefold() for i in catalog]
dupes = {n for n in names if names.count(n) > 1}
checks.append((f"No duplicate names ({len(dupes)} found)", len(dupes) == 0))

# 7. Stateless
chat_code = (ROOT / "app" / "services" / "chat_service.py").read_text(encoding="utf-8")
sess_kws = ["session", "cache", "store", "previous_state", "self.state", "self.memory"]
found = [kw for kw in sess_kws if kw in chat_code.lower()]
checks.append((f"ChatService stateless (found: {found})", len(found) == 0))

# 8. Turn cap
main_code = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
has_cap = "len(request_body.messages) > 8" in main_code
checks.append((f"Turn cap at 8 messages", has_cap))

# 9. Router handles all routes
router = RuleBasedRouter()
all_ok = True
for label, state in [
    ("RECOMMEND", ConversationState(role="Engineer", technical_skills=["Python"])),
    ("REFUSE", ConversationState(scope_flag="off_topic")),
    ("COMPARE", ConversationState(comparison_requested=True, mentioned_assessment_names=["Test"])),
    ("CLARIFY", ConversationState()),
    ("REFINE", ConversationState(refinement_detected=True)),
]:
    try:
        d = router.route(state)
        checks.append((f"Router handles {label} -> {d.route.name}", True))
    except Exception as e:
        checks.append((f"Router handles {label}", False))
        all_ok = False

# 10. OpenAPI schema
from app.main import create_app
app = create_app()
oapi = app.openapi()
paths = list(oapi.get("paths", {}).keys())
checks.append(("/chat in OpenAPI", "/chat" in paths))
checks.append(("/health in OpenAPI", "/health" in paths))

# Print results
print("\n=== HARD EVALUATION RESULTS ===\n")
all_pass = True
for name, result in checks:
    status = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print(f"  [{status}] {name}")

print(f"\n{'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
print(f"Total: {len(checks)} checks, {sum(1 for _,r in checks if r)} passed, {sum(1 for _,r in checks if not r)} failed")
