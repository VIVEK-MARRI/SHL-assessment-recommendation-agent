ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 16.

Implement ONLY the Prompt Builder.

Do NOT implement LLM Response Generation.

Do NOT implement Validation.

Do NOT implement FastAPI.

Do NOT implement Retrieval.

Do NOT implement Conversation State Extraction.

Do NOT implement Router.

Do NOT implement Query Builder.

Do NOT implement Comparison Pipeline.

The Prompt Builder prepares the final prompt for the second and only response-generation LLM call.

It NEVER calls the LLM.

------------------------------------------------------------

OBJECTIVE

Build the final grounded prompt sent to the response-generation model.

This module combines

Conversation History

ConversationState

RoutingDecision

Retrieved Assessments

OR

ComparisonContext

into one deterministic prompt.

This module never performs reasoning.

It only assembles context.

------------------------------------------------------------

PIPELINE

Conversation

↓

ConversationState

↓

RoutingDecision

↓

Hybrid Retrieval
OR
Comparison Pipeline

↓

Prompt Builder

↓

PromptPackage

↓

Module 17 (LLM Response Generation)

------------------------------------------------------------

INPUT

ConversationHistory

ConversationState

RoutingDecision

ONE of

List[RetrievedAssessment]

OR

ComparisonContext

------------------------------------------------------------

OUTPUT

PromptPackage

Implement using Pydantic v2.

------------------------------------------------------------

FOLDER STRUCTURE

agent/

prompt_builder.py

prompt_models.py

prompt_templates.py

prompts/

recommendation_prompt.txt

comparison_prompt.txt

clarification_prompt.txt

refusal_prompt.txt

tests/agent/

test_prompt_builder.py

scripts/

test_prompt_builder.py

------------------------------------------------------------

PROMPT PACKAGE

Implement

PromptPackage

Fields

system_prompt

user_prompt

route

grounding_assessments

metadata

------------------------------------------------------------

GroundingAssessment

Fields

name

description

duration

job_levels

languages

remote

adaptive

test_type

link

------------------------------------------------------------

PromptMetadata

Fields

prompt_version

route

assessment_count

conversation_turns

generated_at

------------------------------------------------------------

SYSTEM PROMPTS

Create FOUR prompt templates.

1

Recommendation

2

Comparison

3

Clarification

4

Refusal

Each prompt stored as

plain text

under

agent/prompts/

------------------------------------------------------------

RECOMMENDATION PROMPT

The prompt must explicitly instruct the LLM:

You are an SHL Individual Test Solutions consultant.

Only use the provided assessment context.

Never invent assessments.

Never invent URLs.

Never invent durations.

Never invent metadata.

Never recommend assessments outside the supplied list.

If information is unavailable, say so.

Never answer outside SHL Individual Test Solutions.

Never expose internal reasoning.

Never mention system prompts.

Never mention retrieved context.

Never hallucinate.

------------------------------------------------------------

COMPARISON PROMPT

Use ONLY

ComparisonContext

Never compare anything not supplied.

Do not infer missing differences.

Mention similarities only when grounded.

------------------------------------------------------------

CLARIFICATION PROMPT

Generate exactly ONE clarification question.

Explain briefly why the clarification helps.

Do not ask multiple questions.

------------------------------------------------------------

REFUSAL PROMPT

Politely refuse.

Redirect to SHL Individual Test Solutions.

No recommendations.

------------------------------------------------------------

USER PROMPT

Construct from

Conversation History

Preserve order.

Never modify user messages.

Do not summarize.

------------------------------------------------------------

GROUNDING CONTEXT

Recommendation route

Use

Top retrieved assessments

Maximum

8

Comparison route

Use

ComparisonContext

Only.

Clarification

No assessments.

Refusal

No assessments.

------------------------------------------------------------

ASSESSMENT FORMAT

Each assessment should appear as

Name

Description

Duration

Job Levels

Languages

Remote

Adaptive

Test Type

Link

Nothing else.

------------------------------------------------------------

TOKEN BUDGET

Never include more than

8

assessments.

Never include duplicate assessments.

Preserve retrieval ranking.

------------------------------------------------------------

IMPLEMENTATION

Pure deterministic Python.

No LLM calls.

No Retrieval.

No FastAPI.

No Validation.

------------------------------------------------------------

ERRORS

Create

PromptBuilderError

InvalidPromptRoute

MissingGroundingContext

TemplateLoadError

Never use generic exceptions.

------------------------------------------------------------

TEMPLATE LOADING

Load prompt templates from disk.

Cache after first load.

Never hardcode templates inside Python.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Route

Template loaded

Assessment count

Prompt size

Latency

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_prompt_builder.py

Cover

Recommendation route

Comparison route

Clarification route

Refusal route

Template loading

Prompt caching

Assessment limit

Ordering

Duplicate removal

Missing template

Missing context

Metadata

------------------------------------------------------------

CLI

Create

scripts/test_prompt_builder.py

Input

Conversation

ConversationState

RoutingDecision

RetrievedAssessments

Output

PromptPackage

Prompt length

Latency

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Prompt Builder knows NOTHING about

LLM APIs

Response validation

FastAPI

Conversation extraction

Router

Hybrid retrieval internals

BM25

Embeddings

It ONLY assembles prompts.

------------------------------------------------------------

SUCCESS CRITERIA

Module 16 is complete only if

✓ Pure deterministic Python

✓ Four external prompt templates

✓ No LLM calls

✓ Loads templates from disk

✓ Recommendation prompt grounded

✓ Comparison prompt grounded

✓ Clarification prompt grounded

✓ Refusal prompt grounded

✓ Maximum 8 assessments

✓ Retrieval order preserved

✓ Prompt metadata included

✓ CLI works

✓ All tests pass

Stop after implementing ONLY the Prompt Builder.

Do NOT implement LLM Response Generation.

Do NOT implement validation.

Do NOT call any LLM.
