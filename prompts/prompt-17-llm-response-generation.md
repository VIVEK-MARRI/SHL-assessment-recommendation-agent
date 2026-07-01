ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 17.

Implement ONLY the LLM Response Generation module.

Do NOT implement Validation.

Do NOT implement Response Builder.

Do NOT implement FastAPI.

Do NOT implement Prompt Builder.

Do NOT implement Retrieval.

Do NOT implement Conversation State Extraction.

Do NOT implement Router.

Do NOT implement Query Builder.

Do NOT implement Comparison Pipeline.

This module performs the SECOND and FINAL LLM call.

No additional LLM calls are ever permitted.

------------------------------------------------------------

OBJECTIVE

Execute exactly one grounded LLM request using the PromptPackage produced by Module 16.

This module NEVER performs retrieval.

This module NEVER loads the catalog.

This module NEVER validates recommendations.

This module NEVER constructs API responses.

Its ONLY responsibility is

PromptPackage

↓

LLM

↓

LLMGenerationResult

------------------------------------------------------------

PIPELINE

PromptPackage

↓

LLM Client

↓

Structured JSON Response

↓

LLMGenerationResult

↓

(Module 18 Validator)

------------------------------------------------------------

INPUT

PromptPackage

------------------------------------------------------------

OUTPUT

LLMGenerationResult

Implement using Pydantic v2.

------------------------------------------------------------

FOLDER STRUCTURE

agent/

generation.py

generation_models.py

generation_client.py

tests/agent/

test_generation.py

test_generation_client.py

scripts/

test_generation.py

------------------------------------------------------------

LLM CLIENT

Reuse the provider abstraction created in Module 12.

Support

Groq

OpenRouter

The provider must be dependency injected.

Never hardcode provider logic.

------------------------------------------------------------

RESPONSE MODEL

Implement

LLMGenerationResult

Fields

reply: str

recommended_names: list[str]

end_of_conversation: bool

provider

model

latency_ms

tokens_prompt

tokens_completion

tokens_total

finish_reason

------------------------------------------------------------

LLM OUTPUT CONTRACT

The model MUST return JSON only.

Schema

{
  "reply": "...",
  "recommended_names": [
      "Assessment Name"
  ],
  "end_of_conversation": true
}

No additional fields allowed.

------------------------------------------------------------

CRITICAL RULES

The LLM MUST NEVER return

URLs

test_type

entity_id

duration

languages

job_levels

metadata

Only assessment names.

------------------------------------------------------------

SYSTEM ENFORCEMENT

Append these instructions to every request.

Return ONLY valid JSON.

Do not wrap JSON in markdown.

Do not explain your reasoning.

Do not output chain-of-thought.

Only recommend assessments provided in the grounding context.

Never invent assessment names.

Never output URLs.

Never output metadata.

------------------------------------------------------------

GROUNDING

Recommendation route

Uses

PromptPackage.grounding_assessments

Comparison route

Uses

ComparisonContext

Clarification

Uses

Conversation only

Refusal

Uses

Conversation only

------------------------------------------------------------

JSON PARSING

Implement strict parsing.

Reject

Markdown

Code fences

Malformed JSON

Trailing text

Unknown fields

Retry

ONE time only

ONLY when

JSON parsing fails.

Never retry for semantic errors.

------------------------------------------------------------

TIMEOUT

Maximum request timeout

20 seconds.

------------------------------------------------------------

RETRY POLICY

Retry only once.

Allowed retry condition

Malformed JSON

Connection reset

HTTP 429

HTTP 503

Network timeout

Never retry

Hallucinated names

Validation failures

Unknown assessments

------------------------------------------------------------

ERRORS

Create

GenerationError

ProviderError

JSONGenerationError

GenerationTimeoutError

RateLimitError

Never use generic exceptions.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Provider

Model

Latency

Prompt tokens

Completion tokens

Retry

Finish reason

Never log API keys.

Never log full prompts.

Never log user PII.

------------------------------------------------------------

IMPLEMENTATION

Pure orchestration.

No Retrieval.

No Catalog.

No Validation.

No Response Builder.

No FastAPI.

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_generation.py

test_generation_client.py

Cover

Successful response

Malformed JSON

Markdown JSON

Retry success

Retry failure

HTTP 429

HTTP 503

Timeout

Connection error

Provider error

Unknown fields

Empty recommendations

Recommendation route

Comparison route

Clarification route

Refusal route

------------------------------------------------------------

CLI

Create

scripts/test_generation.py

Input

PromptPackage JSON

Output

LLMGenerationResult

Latency

Provider

Model

Token usage

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Generation module knows NOTHING about

Catalog

Hybrid Retrieval

BM25

Embeddings

Validator

FastAPI

Response Builder

It ONLY performs

PromptPackage

↓

LLM

↓

Structured JSON

------------------------------------------------------------

SUCCESS CRITERIA

Module 17 is complete only if

✓ Exactly one LLM call

✓ No retrieval

✓ No catalog access

✓ Strict JSON parsing

✓ One retry only

✓ Provider abstraction reused

✓ Timeout enforced

✓ Structured response model

✓ No metadata returned

✓ No URLs returned

✓ CLI works

✓ All tests pass

Stop after implementing ONLY the LLM Response Generation module.

Do NOT implement Validator.

Do NOT implement Response Builder.

Do NOT implement FastAPI.

Do NOT redesign the architecture.
