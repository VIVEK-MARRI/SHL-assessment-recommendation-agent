# Prompt 11 - Hybrid Retrieval Engine (Module 11)

## Role

Continue following ALL previous prompts without exception.

This is Implementation Module 11.

Implement ONLY the Hybrid Retrieval Engine.

Do NOT implement ConversationState.
Do NOT implement FastAPI.
Do NOT implement routing.
Do NOT implement prompt engineering.
Do NOT implement LLM integration.
Do NOT implement response generation.
Do NOT implement validation.

This module is responsible ONLY for combining semantic retrieval and lexical retrieval into a single ranked result set.

---

## Objective

Build a deterministic Hybrid Retrieval Engine.

The pipeline is:

```text
User Query
  |
EmbeddingRetriever.search()
  |
BM25Retriever.search()
  |
Reciprocal Rank Fusion (RRF)
  |
Deduplication
  |
Confidence Gate
  |
Hybrid Results
```

This module must NEVER directly access FAISS.

This module must NEVER directly access BM25.

It must ONLY consume the two retriever APIs built in Modules 09 and 10.

---

## Input

Use ONLY:

- `EmbeddingRetriever.search()`
- `BM25Retriever.search()`

Do NOT load indexes directly.

---

## Output

Return:

```python
List[RetrievedAssessment]
```

Reuse `retrieval/retrieval_models.py`.

Do NOT create another result model.

---

## Folder Structure

```text
retrieval/
  hybrid_retriever.py
  reciprocal_rank_fusion.py
  confidence_gate.py
```

Do not modify previous modules except for compatibility.

---

## Retrieval Flow

```text
User Query
  |
EmbeddingRetriever.search(query)
  |
BM25Retriever.search(query)
  |
Reciprocal Rank Fusion
  |
Merge metadata
  |
Deduplicate
  |
Confidence Gate
  |
Top K
```

---

## Reciprocal Rank Fusion

Implement standard RRF.

Formula:

```text
RRF Score = sum(1 / (k + rank))
```

Use:

```text
k = 60
```

Do NOT tune this.

Use the standard value.

---

## Input To RRF

Embedding Retriever already provides `embedding_rank`.

BM25 Retriever already provides `bm25_rank`.

Use those.

Never recompute rankings.

---

## Merging

Merge by `entity_id`.

Do NOT merge by `name`.

Do NOT merge by `url`.

Every assessment should appear only once.

---

## Final Score

Each `RetrievedAssessment` should now include:

- `rrf_score`
- `retrieval_source = "hybrid"`

Keep:

- `embedding_rank`
- `bm25_rank`

Keep original score fields if already present.

Do NOT discard metadata.

---

## Confidence Gate

Implement `ConfidenceGate`.

Purpose: prevent weak recommendations.

Configuration:

- `minimum_rrf_score`
- `minimum_overlap`

Rules:

- If top result RRF score is below threshold, confidence is low.
- If Embedding and BM25 have zero overlap, confidence is low.
- If too few retrieved assessments are available, confidence is low.

Return `HybridRetrievalResult`.

Fields:

- `results`
- `confidence`
- `reason`

---

## Confidence Levels

- `HIGH`
- `MEDIUM`
- `LOW`

Reason examples:

- Strong agreement
- Weak lexical support
- Weak semantic support
- Insufficient evidence

---

## Hybrid Retriever

Expose `HybridRetriever`.

Methods:

- `initialize()`
- `search()`
- `health()`

`health()` returns:

- `embedding_ready`
- `bm25_ready`
- `rrf_ready`
- `catalog_sha256`
- `embedding_model`
- `tokenizer_version`
- `average_latency_ms`

---

## Logging

Use `logging.getLogger(__name__)`.

Log:

- Embedding retrieval completed
- BM25 retrieval completed
- RRF fusion completed
- Deduplication completed
- Confidence evaluation completed
- Results returned
- Execution time

Never use `print()`.

---

## Error Handling

Handle:

- Embedding retriever unavailable
- BM25 retriever unavailable
- Catalog mismatch
- SHA mismatch
- Metadata mismatch
- Empty retrieval
- RRF failure

Never silently continue.

Raise:

- `HybridRetrieverError`
- `RRFError`
- `ConfidenceGateError`

---

## Unit Tests

Create:

```text
tests/retrieval/
  test_rrf.py
  test_confidence_gate.py
  test_hybrid_retriever.py
```

Cover:

- Correct RRF score calculation
- Duplicate merging
- Entity merge
- Rank preservation
- Confidence HIGH
- Confidence MEDIUM
- Confidence LOW
- No overlap
- Partial overlap
- Empty retrieval
- Latency
- Deterministic output
- Health endpoint

---

## CLI

Create `scripts/test_hybrid_search.py`.

Execute:

- Java Developer
- Python Backend
- Sales Manager
- Leadership Assessment
- Customer Service

Display:

- Embedding Rank
- BM25 Rank
- RRF Score
- Confidence
- Top Results
- Execution Time

---

## Verification

Run:

```bash
py scripts/test_hybrid_search.py
pytest tests/retrieval/
```

Verify:

- No duplicate assessments
- Correct RRF scores
- Confidence gate working
- Ranking deterministic

Report:

- Embedding latency
- BM25 latency
- Hybrid latency
- Average overlap
- Tests passed
- Tests failed

---

## Architectural Constraints

Hybrid Retriever must NEVER:

- Load FAISS
- Load BM25
- Tokenize
- Generate embeddings

It ONLY orchestrates:

- `EmbeddingRetriever`
- `BM25Retriever`
- Reciprocal Rank Fusion

---

## Implementation Quality

Use:

- Pydantic v2
- SOLID
- Dependency Injection
- Google-style docstrings
- Type hints

No TODOs.

No placeholder implementations.

Production-grade code only.

---

## Success Criteria

Module 11 is complete only if:

- EmbeddingRetriever reused
- BM25Retriever reused
- Standard RRF implemented
- Merge by entity_id
- No duplicate assessments
- `rrf_score` populated
- `retrieval_source="hybrid"`
- Confidence Gate implemented
- Health endpoint works
- CLI works
- All tests pass

Do NOT implement ConversationState.

Do NOT implement routing.

Do NOT implement LLMs.

Stop after completing the Hybrid Retrieval Engine.
