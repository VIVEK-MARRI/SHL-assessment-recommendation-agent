"""Debug the 5 failing scenarios."""
import json, time, requests, os

API_URL = os.getenv("API_URL", "http://localhost:8000")
ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
catalog = json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))
catalog_names = {i["name"].casefold() for i in catalog}

def chat(msgs, retries=3):
    for a in range(retries):
        r = requests.post(f"{API_URL}/chat", json={"messages": msgs}, timeout=60)
        if r.status_code == 429:
            time.sleep(15)
            continue
        return r.status_code, r.json()
    return 429, {}

tests = [
    ("Clarify: Role 'Assess an engineer'", [{"role": "user", "content": "Assess an engineer."}]),
    ("Compare: Python vs Java", [{"role": "user", "content": "Compare Python (New) and Java (New)."}]),
    ("Edge: Single 'Python'", [{"role": "user", "content": "Python"}]),
    ("Edge: Cognitive", [{"role": "user", "content": "Need cognitive ability tests."}]),
    ("Edge: 30min", [{"role": "user", "content": "Python tests under 30 minutes."}]),
]

for name, msgs in tests:
    print(f"\n=== {name} ===")
    status, data = chat(msgs)
    print(f"Status: {status}")
    print(f"Reply: {data.get('reply', '')[:200]}")
    recs = data.get("recommendations")
    if recs:
        print(f"Recommendations ({len(recs)}):")
        for r in recs:
            in_cat = "OK" if r["name"].casefold() in catalog_names else "HALLUCINATION"
            print(f"  - {r['name']} [{in_cat}]")
    else:
        print("Recommendations: None")
    time.sleep(20)
