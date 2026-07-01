# Prompt 07 – Embedding Index Builder (Module 07)

## Role

Continue following ALL previous prompts without exception.

This is Implementation Module 07.

Implement ONLY the Embedding Index Builder.

Do NOT implement retrieval.
Do NOT implement BM25.
Do NOT implement Hybrid Retrieval.
Do NOT implement RRF.
Do NOT implement ConversationState.
Do NOT implement FastAPI.
Do NOT implement routing.
Do NOT implement prompt engineering.
Do NOT implement LLM integration.

This module is responsible ONLY for converting the canonical SHL catalog into a persistent semantic vector index.

---

## Objective

Build a deterministic embedding indexing pipeline.

```
catalog/catalog.json
        ↓
    Load Assessments
        ↓
    Construct Search Documents
        ↓
    Generate Embeddings
        ↓
    Build FAISS Index
        ↓
    Persist Index
```

Every downstream retrieval module must reuse this index.
No downstream module should regenerate embeddings.

---

## Input

The canonical catalog already exists.

Location: `catalog/catalog.json`

This is the ONLY catalog consumed by this module.
Never read `catalog/raw_catalog.json`.

---

## Output

Generate:

```
indexes/
├── embedding.index
├── embedding_metadata.json
└── embedding_config.json
```

These files become the persistent semantic search index.

---

## Folder Structure

```
retrieval/
├── __init__.py
├── constants.py
├── models.py
├── text_builder.py
├── embedding_generator.py
├── embedding_index.py
├── index_loader.py
└── index_builder.py

indexes/
├── embedding.index
├── embedding_metadata.json
└── embedding_config.json
```

---

## Embedding Model

Use `sentence-transformers`.

Model: `BAAI/bge-small-en-v1.5`

Requirements:
- local model
- free
- deterministic
- no API dependency

Load once. Reuse across the pipeline. Never reload for each assessment.

---

## Text Construction

Every assessment must become exactly ONE semantic document.

Construct the embedding text using:
- Assessment Name
- Description
- Categories (keys)
- Job Levels
- Languages
- Duration
- Status
- Remote
- Adaptive

**Format:**

```
Name:
...

Description:
...

Categories:
...

Job Levels:
...

Languages:
...

Duration:
...

Status:
...

Remote:
...

Adaptive:
...
```

Never include URLs.
Never include entity IDs.
URLs are identifiers, not semantic content.

---

## Embedding Generation

- Generate one embedding per assessment.
- Batch encoding required.
- Batch size configurable.
- Normalize embeddings.
- Use cosine similarity.
- Do not use GPU-specific code.
- The implementation must run on CPU.

---

## FAISS Index

Create `IndexFlatIP` because normalized embeddings with inner product equal cosine similarity.

Persist: `embedding.index`

---

## Metadata

Generate `embedding_metadata.json`.

Each record must include:
- `entity_id`
- `name`
- `url`
- `test_type`
- `offset`

No embedding vectors inside metadata.

---

## Config

Generate `embedding_config.json`.

Store:
- embedding model
- embedding dimension
- catalog version
- creation timestamp
- number of assessments
- batch size

---

## Index Loader

Implement `load_embedding_index()`.

Responsibilities:
- Load FAISS index
- Load metadata
- Load config
- Verify consistency
- Raise informative exceptions

---

## Text Builder

Implement `build_document(assessment)`.

Returns a single deterministic string.
Unit test this carefully.

---

## Logging

Use `logging.getLogger(__name__)`. Never use `print()`.

Log:
- Catalog loaded
- Documents built
- Embeddings generated
- Index created
- Index saved
- Execution time

---

## Error Handling

Handle:
- Missing catalog
- Corrupted catalog
- Embedding model loading failure
- FAISS write failure
- Metadata mismatch
- Configuration mismatch

Never silently continue.

---

## Unit Tests

Create `tests/retrieval/`.

Include tests for:
- Text Builder
- Embedding Generator
- Metadata
- Index Creation
- Index Loading
- Configuration
- Persistence
- Corrupted Index
- Missing Catalog
- Deterministic Embeddings

---

## Implementation Quality

- Pydantic v2
- SOLID principles
- Google-style docstrings
- Type hints
- No TODOs
- No placeholder implementations
- No dead code
- Production quality only

---

## CLI

Create `scripts/build_embedding_index.py`.

The script must only call `retrieval.build_embedding_index()`.
No business logic inside the script.

---

## Verification

After implementation, run:

```
py scripts/build_embedding_index.py
```

Verify that:
```
indexes/embedding.index
indexes/embedding_metadata.json
indexes/embedding_config.json
```
are generated.

Run `pytest tests/retrieval/`.

Report:
- assessments indexed
- embedding dimension
- index size
- total tests
- passed
- failed

Only after successful verification declare Module 07 complete.

Do not implement retrieval.
Do not implement BM25.
Do not implement hybrid retrieval.
Stop after the Embedding Index Builder.
