ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 19.

Implement ONLY the Response Builder.

Do NOT implement FastAPI.

Do NOT implement Validation.

Do NOT implement Retrieval.

Do NOT implement Prompt Builder.

Do NOT implement LLM Generation.

Do NOT implement Conversation State Extraction.

Do NOT implement Router.

Do NOT implement Query Builder.

Do NOT implement Comparison Pipeline.

This module assembles the final API response.

No LLM calls are allowed.

------------------------------------------------------------

OBJECTIVE

The Response Builder converts the validated generation result into the exact response schema required by the SHL assignment.

This module is the ONLY place allowed to inject catalog metadata (URL and test_type).

It NEVER validates.

It NEVER retrieves.

It NEVER performs fuzzy matching.

It NEVER modifies the conversational reply.

------------------------------------------------------------

PIPELINE

ValidatedGenerationResult

↓

Catalog Lookup

↓

Response Builder

↓

ChatResponse

↓

Module 20 (FastAPI)

------------------------------------------------------------

INPUT

ValidatedGenerationResult

RoutingDecision

------------------------------------------------------------

OUTPUT

ChatResponse

Implement using Pydantic v2.

------------------------------------------------------------

FOLDER STRUCTURE

agent/

response_builder.py

response_models.py

response_catalog.py

tests/agent/

test_response_builder.py

test_response_catalog.py

scripts/

test_response_builder.py

------------------------------------------------------------

LOAD CATALOG

Load ONLY

catalog/catalog.json

Never load

raw_catalog.json

Cache after first load.

------------------------------------------------------------

CHAT RESPONSE MODEL

Implement

Recommendation

Fields

name

url

test_type

------------------------------------------------------------

ChatResponse

Fields

reply: str

recommendations: Optional[list[Recommendation]]

------------------------------------------------------------

IMPORTANT

recommendations

MUST follow SHL sample conversations.

For

CLARIFY

↓

recommendations = null

For

REFUSE

↓

recommendations = null

For

RECOMMEND

↓

recommendations = list

For

REFINE

↓

recommendations = list

For

COMPARE

↓

recommendations = list

Never return an empty list.

------------------------------------------------------------

CATALOG LOOKUP

Lookup

validated_names

using

catalog.json

Inject ONLY

name

url

test_type

Do NOT inject

description

duration

languages

job_levels

adaptive

remote

------------------------------------------------------------

TEST TYPE

Use the

test_type

already generated in

catalog.json

Do NOT derive it again.

------------------------------------------------------------

ORDERING

Preserve

validated_names

order exactly.

------------------------------------------------------------

REPLY

Never modify

reply.

Pass through exactly.

------------------------------------------------------------

RECOMMENDATION LIMIT

Maximum

10

recommendations.

Never exceed.

------------------------------------------------------------

IMPLEMENTATION

Pure deterministic Python.

No LLM.

No Retrieval.

No Prompt Builder.

No Validation.

No FastAPI.

------------------------------------------------------------

ERRORS

Create

ResponseBuilderError

CatalogLookupError

InvalidValidatedResult

CatalogLoadError

Never use generic exceptions.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Catalog loaded

Recommendations injected

Recommendation count

Route

Latency

Never log prompts.

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_response_builder.py

test_response_catalog.py

Cover

Recommend route

Refine route

Compare route

Clarify route

Refuse route

Catalog lookup

Ordering

Recommendation limit

Null recommendations

Missing catalog record

Catalog cache

------------------------------------------------------------

CLI

Create

scripts/test_response_builder.py

Input

ValidatedGenerationResult JSON

RoutingDecision JSON

Output

ChatResponse JSON

Latency

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Response Builder knows NOTHING about

LLMs

Hybrid Retrieval

BM25

Embeddings

Prompt Builder

Validator internals

FastAPI

It ONLY converts

ValidatedGenerationResult

↓

ChatResponse

------------------------------------------------------------

SUCCESS CRITERIA

Module 19 is complete only if

✓ Pure deterministic Python

✓ Loads only catalog.json

✓ Catalog cached

✓ URLs injected only here

✓ test_type injected only here

✓ recommendations=null for clarify/refuse

✓ Recommendation order preserved

✓ Maximum 10 recommendations

✓ CLI works

✓ All tests pass

Stop after implementing ONLY the Response Builder.

Do NOT implement FastAPI.

Do NOT implement API endpoints.

Do NOT perform validation.

Do NOT call any LLM.
