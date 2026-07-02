import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/chat"

def test_bug_2():
    print("\n--- Testing Bug 2 (Off-topic refusal) ---")
    resp = requests.post(BASE_URL, json={'messages': [{'role': 'user', 'content': 'Who won the FIFA World Cup?'}]})
    data = resp.json()
    print("Response:", data)
    assert data.get("recommendations") is None
    # Usually off-topic prompts the agent to say it only helps with SHL assessments
    assert "SHL" in data.get("reply", "") or "assessment" in data.get("reply", "").lower() or "not" in data.get("reply", "")

def test_bug_1_4_5():
    print("\n--- Testing Bug 1, 4, 5 (State Overwrite, Query Builder) ---")
    messages = [
        {'role': 'user', 'content': 'I need assessments for Python Developers.'},
        {'role': 'assistant', 'content': 'I recommend Python.'},
        {'role': 'user', 'content': 'Actually I\'m hiring Java Developers instead.'}
    ]
    resp = requests.post(BASE_URL, json={'messages': messages})
    data = resp.json()
    print("Response:", data)
    reply = data.get("reply", "")
    assert data.get("recommendations") is not None or "not provide enough information" in reply
    if data.get("recommendations"):
        recs = data["recommendations"]
        names = [r["name"].lower() for r in recs]
        assert any("java" in n for n in names)
        assert not any("python" in n for n in names)

def test_bug_3_6():
    print("\n--- Testing Bug 3, 6 (Retrieval Pollution & Prompt Grounding) ---")
    messages = [
        {'role': 'user', 'content': 'I need assessments for Python Developers.'}
    ]
    resp = requests.post(BASE_URL, json={'messages': messages})
    data = resp.json()
    print("Response:", data)
    recs = data.get("recommendations", [])
    names = [r["name"].lower() for r in recs]
    print("Recommendations:", names)
    assert any("python" in n for n in names)
    assert not any("mulesoft" in n for n in names)
    assert not any("drupal" in n for n in names)

def test_bug_7():
    print("\n--- Testing Bug 7 (Comparison) ---")
    messages = [
        {'role': 'user', 'content': 'Compare OPQ32r and Verify Interactive.'}
    ]
    resp = requests.post(BASE_URL, json={'messages': messages})
    data = resp.json()
    print("Response:", data)
    recs = data.get("recommendations")
    assert recs is not None
    names = [r["name"].lower() for r in recs]
    assert any("opq32" in n for n in names)
    assert any("verify interactive" in n for n in names)

def test_bug_8():
    print("\n--- Testing Bug 8 (Turn Cap) ---")
    messages = []
    for _ in range(9):
        messages.append({'role': 'user', 'content': 'hello'})
        messages.append({'role': 'assistant', 'content': 'hi'})
    messages.append({'role': 'user', 'content': 'hello'})
    
    resp = requests.post(BASE_URL, json={'messages': messages})
    print("Status:", resp.status_code)
    data = resp.json()
    print("Response:", data)
    assert resp.status_code == 200
    assert "maximum allowed length" in data.get("reply", "")
    assert data.get("recommendations") is None

if __name__ == "__main__":
    test_bug_2()
    test_bug_1_4_5()
    test_bug_3_6()
    test_bug_7()
    test_bug_8()
    print("\nAll live bug tests passed!")
