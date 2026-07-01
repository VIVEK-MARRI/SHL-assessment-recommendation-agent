ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 15.

Implement ONLY the Comparison Pipeline.

Do NOT implement Prompt Builder.

Do NOT implement Response Generation.

Do NOT implement FastAPI.

Do NOT implement Validation.

Do NOT implement Retrieval.

Do NOT implement Hybrid Retrieval.

Do NOT implement Conversation State Extraction.

Do NOT implement the Router.

Do NOT implement Query Builder.

The Comparison Pipeline must be completely deterministic.

No LLM calls are allowed.

------------------------------------------------------------

OBJECTIVE

The Comparison Pipeline resolves assessment names mentioned by the user into canonical catalog records.

Comparison is NOT retrieval.

Comparison NEVER uses

EmbeddingRetriever

BM25Retriever

HybridRetriever

Comparison always works directly against the canonical catalog.

------------------------------------------------------------

PIPELINE

ConversationState

↓

mentioned_assessment_names

↓

Catalog Resolver

↓

RapidFuzz Candidate Search

↓

Exact Catalog Match

↓

Comparison Context

↓

(Module 16 Prompt Builder)

------------------------------------------------------------

INPUT

ConversationState

RoutingDecision

------------------------------------------------------------

OUTPUT

ComparisonContext

Use Pydantic v2.

------------------------------------------------------------

FOLDER STRUCTURE

agent/

comparison.py

comparison_models.py

catalog_matcher.py

tests/agent/

test_catalog_matcher.py

test_comparison.py

scripts/

test_comparison.py

------------------------------------------------------------

LOAD CATALOG

Load ONLY

catalog/catalog.json

Never use

raw_catalog.json

Load once.

Cache in memory.

------------------------------------------------------------

MATCHING STRATEGY

Step 1

Case-insensitive exact match

↓

Step 2

Normalized exact match

(remove extra whitespace)

↓

Step 3

RapidFuzz

WRatio

Threshold

90

↓

Step 4

Reject

Do NOT guess.

------------------------------------------------------------

DO NOT

Search embeddings.

Search BM25.

Search Hybrid Retrieval.

------------------------------------------------------------

COMPARISON CONTEXT

Implement

ComparisonAssessment

Fields

entity_id

name

url

test_type

description

job_levels

languages

duration

remote

adaptive

keys

------------------------------------------------------------

ComparisonContext

Fields

matched_assessments

unmatched_names

comparison_possible

reason

------------------------------------------------------------

MATCHING RULES

If

one assessment found

comparison_possible = false

reason =

"Need at least two assessments."

If

two or more assessments found

comparison_possible = true

------------------------------------------------------------

UNMATCHED

Never invent.

Never hallucinate.

Example

User

Compare Rust Assessment

↓

Rust Assessment

not found

↓

unmatched_names

contains

Rust Assessment

------------------------------------------------------------

NORMALIZATION

Normalize

Whitespace

Unicode NFKC

Case

Keep deterministic.

------------------------------------------------------------

RAPIDFUZZ

Use

rapidfuzz.process.extractOne

or

extract

Metric

WRatio

Threshold

90

Never lower threshold.

------------------------------------------------------------

SORTING

Preserve

User order.

Never reorder.

------------------------------------------------------------

IMPLEMENTATION

Pure deterministic Python.

No LLM.

No Retrieval.

No Prompt Builder.

No FastAPI.

------------------------------------------------------------

ERRORS

Create

CatalogMatchError

ComparisonError

CatalogLoadError

InvalidComparisonRequest

Never use generic exceptions.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Catalog loaded

Assessment matched

RapidFuzz fallback

Unmatched assessment

Comparison context built

Latency

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_catalog_matcher.py

test_comparison.py

Cover

Exact match

Case-insensitive match

Whitespace normalization

RapidFuzz match

Threshold rejection

Unknown assessment

One assessment

Two assessments

Three assessments

Ordering preserved

Duplicate names

Latency

------------------------------------------------------------

CLI

Create

scripts/test_comparison.py

Input

ConversationState JSON

Output

ComparisonContext

Matched

Unmatched

Latency

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Comparison Pipeline knows NOTHING about

Hybrid Retrieval

BM25

Embeddings

Prompt Builder

LLMs

Validator

FastAPI

Recommendations

It ONLY converts

mentioned_assessment_names

↓

ComparisonContext

------------------------------------------------------------

SUCCESS CRITERIA

Module 15 is complete only if

✓ Pure deterministic Python

✓ Loads only catalog.json

✓ Uses RapidFuzz only as fallback

✓ Exact match preferred

✓ No retrieval used

✓ No LLM

✓ User order preserved

✓ Unknown assessments handled correctly

✓ CLI works

✓ All tests pass

Stop after implementing ONLY the Comparison Pipeline.

Do NOT implement Prompt Builder.

Do NOT generate comparison text.

Do NOT call an LLM.

The output must ONLY be a structured ComparisonContext.
