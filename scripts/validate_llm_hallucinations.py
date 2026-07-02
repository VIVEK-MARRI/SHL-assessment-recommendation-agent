"""Hallucination Validator for LLM Outputs."""
import os
import sys
import time
import requests
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog" / "catalog.json"
REPORTS_DIR = ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "hallucination_report.md"

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # create a fast lookup for exact names and URLs
    names = {item["name"].lower() for item in data}
    urls = {item["link"].lower() for item in data if "link" in item}
    return names, urls

def validate_hallucinations():
    print(f"Running hallucination validation against {BASE_URL}")
    names_catalog, urls_catalog = load_catalog()
    
    test_cases = [
        {"role": "user", "content": "I need a test for Python."},
        {"role": "user", "content": "Looking for Java EE tests."},
        {"role": "user", "content": "Give me something for Data Science and Machine Learning."},
        {"role": "user", "content": "Do you have any leadership assessments?"}
    ]
    
    passed_count = 0
    results = []
    
    for i, msg in enumerate(test_cases):
        print(f"Executing: Query {i+1}")
        try:
            resp = requests.post(f"{BASE_URL}/chat", json={"messages": [msg]}, timeout=30)
            if resp.status_code != 200:
                results.append((f"Query {i+1}", False, f"Status {resp.status_code}"))
                continue
                
            data = resp.json()
            recs = data.get("recommendations")
            
            if not recs:
                # no recs generated, technically no hallucinations but not useful for validation
                results.append((f"Query {i+1}", True, "No recommendations returned"))
                passed_count += 1
                continue
                
            hallucinated_names = []
            hallucinated_urls = []
            
            for rec in recs:
                r_name = rec.get("name", "").lower()
                r_url = rec.get("url", "").lower()
                
                if r_name not in names_catalog:
                    hallucinated_names.append(r_name)
                if r_url and r_url not in urls_catalog:
                    hallucinated_urls.append(r_url)
                    
            if hallucinated_names or hallucinated_urls:
                err = f"Fake names: {hallucinated_names}, Fake URLs: {hallucinated_urls}"
                print(f"  FAIL: {err}")
                results.append((f"Query {i+1}", False, err))
            else:
                print("  PASS")
                passed_count += 1
                results.append((f"Query {i+1}", True, ""))
                
            time.sleep(15)
        except Exception as e:
            print(f"  FAIL: Exception {e}")
            results.append((f"Query {i+1}", False, str(e)))
            
    # Write report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = ["# Hallucination Validation Report", "", f"Total Queries: {len(test_cases)}", f"Passed: {passed_count}", ""]
    report.append("| Query | Status | Error |")
    report.append("|---|---|---|")
    for name, passed, err in results:
        report.append(f"| {name} | {'PASS' if passed else 'FAIL'} | {err} |")
        
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH}")
    
    if passed_count < len(test_cases):
        sys.exit(1)

if __name__ == "__main__":
    validate_hallucinations()
