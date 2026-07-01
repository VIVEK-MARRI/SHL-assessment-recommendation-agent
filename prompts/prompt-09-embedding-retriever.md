# Prompt 09 - Embedding Retriever (Module 09)

## Role

Continue following ALL previous prompts without exception.

This is Implementation Module 09.

Implement ONLY the Embedding Retriever.

Do NOT implement BM25 retrieval.
Do NOT implement Hybrid Retrieval.
Do NOT implement Reciprocal Rank Fusion (RRF).
Do NOT implement ConversationState.
Do NOT implement FastAPI.
Do NOT implement routing.
Do NOT implement prompt engineering.
Do NOT implement LLM integration.

This module is responsible ONLY for semantic retrieval using the persistent FAISS embedding index built in Module 07.

---

## Objective

Build a production-grade semantic retrieval layer.

The retriever must:

```
Query
  |
Generate Query Embedding
  |
Search FAISS
  |
Resolve Metadata
  |
Return Ranked Results
```

The retriever must NEVER regenerate the index.

The retriever must ALWAYS use the persisted index built by Module 07.

---

## Input

Use ONLY:

```
indexes/
├── embedding.index
├── embedding_metadata.json
└── embedding_config.json
```

Never rebuild embeddings.

Never rebuild the FAISS index.

---

## Output

Return strongly typed retrieval results.

The retriever does NOT generate recommendations.

The retriever only returns ranked assessment candidates.

---

## Folder Structure

```
retrieval/
├── embedding_retriever.py
├── embedding_search.py
└── retrieval_models.py
```

Do not modify previous indexing modules unless required for compatibility.

---

## Retrieval Flow

```
User Query
  |
Normalize query
  |
Generate embedding using the same BAAI/bge-small-en-v1.5 model
  |
L2 normalize query vector
  |
Search IndexFlatIP
  |
Retrieve Top-K
  |
Resolve metadata
  |
Return Ranked Results
```

---

## Query Embedding

Reuse the singleton embedding model implemented in Module 07.

Never reload the model.

Never instantiate a second SentenceTransformer.

Generate exactly one normalized embedding vector.

---

## Search

Implement `search_embeddings()`.

Arguments:

```python
query: str
top_k: int = 20
minimum_score: float = 0.0
```

Return:

```python
List[RetrievedAssessment]
```

Search must use FAISS IndexFlatIP.

Search must support configurable Top-K.

Never hardcode K.

---

## Retrieved Result Model

Create `RetrievedAssessment`.

Fields:

- `entity_id`
- `name`
- `url`
- `test_type`
- `score`
- `rank`
- `job_levels`
- `languages`
- `duration`
- `duration_minutes`
- `remote`
- `adaptive`
- `keys`

The score is the cosine similarity returned by FAISS.

Rank starts at 1.

---

## Score Filtering

Support `minimum_score`.

Results below the threshold are removed.

Threshold is configurable.

Do not hardcode.

---

## Sorting

Results must be sorted by:

```
Highest score
  |
Lowest score
```

The returned list must preserve deterministic ordering.

---

## Error Handling

Handle:

- Missing FAISS index
- Missing metadata
- Corrupted index
- Dimension mismatch
- Invalid query
- Model loading failure
- Configuration mismatch

Never silently continue.

Raise explicit exceptions.

---

## Query Normalization

Normalize queries before embedding.

Perform:

- Unicode NFKC
- Whitespace collapse
- Trim

Do NOT:

- stem
- lemmatize
- expand synonyms
- rewrite the query

Query expansion belongs to Module 13.

---

## Logging

Use `logging.getLogger(__name__)`.

Log:

- Retriever initialized
- Query normalized
- Embedding generated
- FAISS search completed
- Results returned
- Execution time

Never use `print()`.

---

## Public API

Expose `EmbeddingRetriever`.

Methods:

- `initialize()`
- `search()`
- `health()`

`health()` returns:

- index loaded
- model loaded
- embedding dimension
- number of indexed assessments
- catalog SHA

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

Production quality only.

---

## Unit Tests

Create:

```
tests/retrieval/
├── test_embedding_retriever.py
└── test_embedding_search.py
```

Cover:

- Initialization
- Singleton model reuse
- Valid query
- Empty query
- Unicode query
- Large query
- Top-K
- Threshold filtering
- Ranking order
- Metadata resolution
- Dimension mismatch
- Corrupted FAISS
- Missing metadata
- Deterministic retrieval

---

## CLI

Create `scripts/test_embedding_search.py`.

The script should:

- Load retriever
- Run several example searches
- Print Top 5 results
- Print similarity scores
- Print execution time

The CLI is ONLY for manual verification.

No business logic inside it.

---

## Verification

Run:

```bash
py scripts/test_embedding_search.py
pytest tests/retrieval/
```

Verify:

- Top results are reasonable
- Scores decrease monotonically
- Metadata resolves correctly
- No duplicated assessments

Report:

- Indexed assessments
- Embedding dimension
- Average query latency
- Total tests
- Passed
- Failed

---

## Architectural Constraints

The Embedding Retriever MUST know NOTHING about:

- BM25
- Hybrid Retrieval
- RRF
- Conversation State
- LLMs
- Routing
- Prompts

It is a pure semantic retrieval component.

Future Module 10 will consume:

- `EmbeddingRetriever.search()`
- `BM25Retriever.search()`

and combine them via Reciprocal Rank Fusion.

---

## Success Criteria

Module 09 is complete only if:

- Persistent FAISS index is loaded
- Singleton embedding model reused
- Query embeddings generated correctly
- Cosine similarity search works
- Metadata resolves correctly
- Top-K configurable
- Threshold filtering works
- Ranked results returned deterministically
- CLI verification succeeds
- All tests pass

Stop after implementing the Embedding Retriever.

Do NOT implement Hybrid Retrieval.
Do NOT implement BM25 Retrieval.
Do NOT implement RRF.
