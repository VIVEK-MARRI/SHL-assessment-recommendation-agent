# Prompt 08 – BM25 Index Builder (Module 08)

## Role

Continue following ALL previous prompts without exception.

This is Implementation Module 08.

Implement ONLY the BM25 Index Builder.

Do NOT implement retrieval.
Do NOT implement Hybrid Retrieval.
Do NOT implement RRF.
Do NOT implement FastAPI.
Do NOT implement ConversationState.
Do NOT implement routing.
Do NOT implement prompt engineering.
Do NOT implement LLM integration.

This module is responsible ONLY for constructing a deterministic lexical search index from the canonical SHL catalog.

---

## Objective

Build a persistent BM25 lexical index.

```
catalog/catalog.json
        ↓
    Load Assessments
        ↓
    Tokenize Documents
        ↓
    Build BM25 Index
        ↓
    Persist Index
```

The index must later be consumed by the Hybrid Retrieval module. No retrieval logic belongs in this module.

---

## Input

Use ONLY `catalog/catalog.json`. Never read `catalog/raw_catalog.json`. Never regenerate embeddings.

---

## Output

Generate:
```
indexes/
├── bm25_index.pkl
├── bm25_documents.json
└── bm25_config.json
```

---

## Folder Structure

```
retrieval/
├── bm25_tokenizer.py
├── bm25_index.py
├── bm25_loader.py
└── bm25_builder.py
```

Do not modify the embedding modules unless absolutely necessary.

---

## BM25 Implementation

Use `rank-bm25`. Specifically `BM25Okapi`. Do not implement BM25 manually.

---

## Tokenization

Implement a deterministic tokenizer.

Requirements:
- Lowercase text
- Unicode NFKC normalization
- Remove punctuation
- Collapse whitespace
- Split into tokens
- Remove empty tokens

Preserve programming language tokens:
- `C++` → `cpp`
- `C#` → `csharp`
- `.NET` → `dotnet`
- `Java 8` → `["java", "8"]`
- `REST APIs` → `["rest", "apis"]`

Never perform stemming. Never perform lemmatization. Never remove stop words.

---

## Document Construction

Reuse the semantic document structure created in `retrieval/text_builder.py`. Do NOT duplicate document generation logic. This guarantees semantic and lexical indexes stay aligned.

---

## Index Building

```
For every assessment
↓
Tokenize document
↓
Build BM25 corpus
↓
Construct BM25Okapi
↓
Persist
```

The corpus order MUST exactly match `embedding_metadata.json`. Document `i` in BM25 must correspond to vector `i` in FAISS.

---

## Persistence

Persist `bm25_index.pkl` using pickle.

Persist `bm25_documents.json` containing:
- `entity_id`
- `tokens`
- `document`

Persist `bm25_config.json` including:
- `catalog_sha256`
- `document_count`
- `tokenizer_version`
- `bm25_library_version`
- `creation_timestamp`

---

## Index Loader

Implement `load_bm25_index()`.

Responsibilities:
- Load BM25 object, documents, config
- Verify document count, catalog SHA, tokenizer version
- Raise explicit exceptions on mismatch

---

## Tokenizer Version

```python
TOKENIZER_VERSION = "1.0"
```

Future tokenizer changes should invalidate the index automatically.

---

## Logging

Use `logging.getLogger(__name__)`. Never use `print()`.

Log: Catalog loaded, Documents built, Tokenization completed, BM25 index created, Persistence completed, Execution time.

---

## Error Handling

Handle: Missing catalog, Missing embedding metadata, Configuration mismatch, Pickle failures, Corrupted index, Invalid documents. Never silently continue.

---

## Unit Tests

Create `tests/retrieval/`. Add:
- `test_bm25_tokenizer.py`
- `test_bm25_index.py`
- `test_bm25_loader.py`
- `test_bm25_builder.py`

Cover: Unicode normalization, Programming language tokens, Version numbers, Acronyms, Technical keywords, Tokenizer determinism, Corpus ordering, Persistence, Configuration, Corrupted pickle, Missing files, SHA mismatch.

---

## CLI

Create `scripts/build_bm25_index.py`. The script must only call `retrieval.build_bm25_index()`. No business logic inside the CLI.

---

## Architectural Constraints

The BM25 corpus order MUST exactly match `embedding_metadata.json`. Future Hybrid Retrieval will combine BM25 results with FAISS results using Reciprocal Rank Fusion. Consistent document ordering across both indexes is mandatory.

---

## Implementation Quality

Pydantic v2, SOLID, Google-style docstrings, Type hints, Deterministic behavior, No TODOs, No placeholder implementations, Production-quality code only.

---

## Success Criteria

Module 08 is complete only if:
- ✓ BM25 index builds successfully
- ✓ Corpus ordering matches embedding metadata
- ✓ SHA verification works
- ✓ Tokenization is deterministic
- ✓ BM25 artifacts persist correctly
- ✓ All unit tests pass
- ✓ CLI executes successfully

Do not implement retrieval. Do not implement Hybrid Retrieval. Do not implement RRF. Stop after the BM25 Index Builder.
