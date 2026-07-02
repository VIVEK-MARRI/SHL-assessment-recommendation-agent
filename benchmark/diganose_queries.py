"""Diagnose root causes for specific observed weaknesses."""
from __future__ import annotations
import json, logging, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.WARNING)

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.retrieval_models import RetrievedAssessment

retriever = HybridRetriever()
retriever.initialize()

with open(ROOT / "catalog" / "catalog.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_by_id = {a["entity_id"]: a for a in cat}
cat_names_by_id = {a["entity_id"]: a["name"] for a in cat}

def trace_query(query: str, label: str = ""):
    print(f"\n{'='*60}")
    print(f"  QUERY: {query}  ({label})")
    print(f"{'='*60}")
    try:
        result = retriever.search(query, top_k=20)
        for i, r in enumerate(result.results[:15], 1):
            cat_entry = cat_by_id.get(r.entity_id, {})
            jls = cat_entry.get("job_levels", [])
            keys = cat_entry.get("keys", [])
            name = cat_names_by_id.get(r.entity_id, r.name)
            print(f"  {i:>2}. [{r.bm25_score or 0:.2f}/{r.embedding_score or 0:.3f}] "
                  f"rrf={r.rrf_score or 0:.4f} score={r.score:.4f} "
                  f"{name}  JL={jls}  KEYS={keys}")
    except Exception as e:
        print(f"  ERROR: {e}")

# 1. Graduate software engineer
trace_query("Graduate software engineer", "Graduate")

# 2. Data Scientist
trace_query("Data Scientist", "Data Science")

# 3. Leadership
trace_query("Leadership assessment", "Leadership")

# 4. Python test
trace_query("Python test", "Python")

# 5. SQL assessment
trace_query("SQL assessment", "SQL")

# 6. Entry level developer
trace_query("Entry level developer", "Entry Level")

# 7. Backend developer
trace_query("Backend developer", "Backend")

# 8. Management
trace_query("Management assessment", "Management")

# Check what Salesforce ranks
trace_query("Data science assessment", "Data Science 2")
