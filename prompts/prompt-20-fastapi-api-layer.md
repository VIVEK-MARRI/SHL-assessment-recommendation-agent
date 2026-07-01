ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 20.

Implement ONLY the FastAPI API layer.

Do NOT implement Retrieval.

Do NOT implement Prompt Builder.

Do NOT implement Validation.

Do NOT implement LLM Generation.

Do NOT implement Conversation State Extraction.

Do NOT implement Router.

Do NOT implement Query Builder.

Do NOT implement Comparison Pipeline.

Do NOT modify any previous modules.

The FastAPI layer must remain a thin transport layer.

------------------------------------------------------------

OBJECTIVE

Expose the SHL conversational recommendation system as a production-grade REST API.

The API MUST contain zero business logic.

All orchestration must be delegated to ChatService.

------------------------------------------------------------

FOLDER STRUCTURE

app/

main.py

api.py

dependencies.py

schemas.py

services/

chat_service.py

tests/api/

test_chat_api.py

test_health_api.py

scripts/

run_server.py

------------------------------------------------------------

ARCHITECTURE

FastAPI

↓

Request Validation

↓

ChatService

↓

Existing Modules

↓

ChatResponse

↓

JSON Response

------------------------------------------------------------

CHAT SERVICE

Create

services/chat_service.py

ChatService

This is the ONLY orchestrator.

Pipeline

ConversationState Extraction

↓

Router

↓

IF

route == RECOMMEND

↓

Query Builder

↓

Hybrid Retriever

↓

Prompt Builder

↓

Generation

↓

Validator

↓

Response Builder

↓

ChatResponse

------------------------------------------------------------

IF

route == REFINE

Same pipeline.

------------------------------------------------------------

IF

route == COMPARE

↓

Comparison Pipeline

↓

Prompt Builder

↓

Generation

↓

Validator

↓

Response Builder

------------------------------------------------------------

IF

route == CLARIFY

↓

Prompt Builder

↓

Generation

↓

Validator

↓

Response Builder

------------------------------------------------------------

IF

route == REFUSE

↓

Prompt Builder

↓

Generation

↓

Validator

↓

Response Builder

------------------------------------------------------------

NO BUSINESS LOGIC

FastAPI endpoints

must NEVER

call

HybridRetriever

StateExtractor

Generation

PromptBuilder

Validator

directly.

Only

ChatService.chat()

------------------------------------------------------------

REQUEST MODEL

Implement

ChatRequest

messages

List[ConversationMessage]

------------------------------------------------------------

RESPONSE MODEL

Use

ChatResponse

from Module 19.

Do NOT duplicate it.

------------------------------------------------------------

ENDPOINTS

GET

/

Returns

{
  "service":"SHL Assessment Recommendation Agent",
  "version":"1.0.0",
  "status":"running"
}

------------------------------------------------------------

GET

/health

Returns

{
  "status":"healthy",
  "catalog_loaded":true,
  "embedding_index_loaded":true,
  "bm25_index_loaded":true,
  "llm_provider":"groq",
  "version":"1.0.0"
}

Use actual component health methods.

------------------------------------------------------------

POST

/chat

Input

ChatRequest

Output

ChatResponse

------------------------------------------------------------

ERROR HANDLING

Global exception handlers.

400

Bad Request

422

Validation Error

429

Rate Limit

500

Internal Error

503

Provider Unavailable

Never expose stack traces.

------------------------------------------------------------

DEPENDENCY INJECTION

Create

AppContainer

Instantiate ONCE

Catalog

HybridRetriever

StateExtractor

Router

QueryBuilder

ComparisonPipeline

PromptBuilder

Generation

Validator

ResponseBuilder

ChatService

FastAPI receives

container.chat_service

------------------------------------------------------------

STARTUP

Use

FastAPI lifespan

Load

Catalog

Embedding Index

BM25 Index

LLM Client

only once.

------------------------------------------------------------

SHUTDOWN

Release

HTTP clients

Thread pools

Any open resources.

------------------------------------------------------------

MIDDLEWARE

Enable

CORS

Compression (GZip)

Request ID

Structured Logging

------------------------------------------------------------

LOGGING

logging.getLogger(__name__)

Log

Method

Path

Status

Latency

Request ID

Errors

Never log prompts.

Never log API keys.

------------------------------------------------------------

OPENAPI

Provide

title

description

version

tags

examples

------------------------------------------------------------

TESTS

Create

tests/api/

test_health_api.py

test_chat_api.py

Cover

Root endpoint

Health endpoint

Successful chat

Invalid request

Empty messages

Malformed JSON

Provider unavailable

Internal error

------------------------------------------------------------

CLI

Create

scripts/run_server.py

Equivalent to

uvicorn app.main:app

with configurable

host

port

reload

------------------------------------------------------------

DOCKER READY

Read

HOST

PORT

LOG_LEVEL

LLM_PROVIDER

API_KEY

from environment.

Never hardcode.

------------------------------------------------------------

SUCCESS CRITERIA

Module 20 is complete only if

✓ Thin FastAPI layer

✓ ChatService orchestrates everything

✓ Dependency injection

✓ Startup loading

✓ Health endpoint

✓ Chat endpoint

✓ Global exception handlers

✓ OpenAPI docs

✓ Tests pass

✓ No business logic inside API

Stop after implementing ONLY the FastAPI layer.

Do NOT implement Evaluation.

Do NOT implement Docker.

Do NOT redesign previous modules.
