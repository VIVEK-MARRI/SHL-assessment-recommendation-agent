ROLE

Continue following all instructions from:

• Prompt 00 — Project Context
• Prompt 01 — Catalog Context
• Prompt 02 — Conversation Behavior

This prompt defines the production architecture.

This architecture is LOCKED.

Do not redesign it.

Do not remove stages.

Do not merge stages.

Do not introduce additional LLM calls.

Do not replace deterministic components with LLM reasoning.

If a future implementation appears to require an architectural change,

stop,

explain why,

and wait for approval.

Never silently modify the architecture.

------------------------------------------------------------

ARCHITECTURE PHILOSOPHY

The system follows a deterministic Retrieval-Augmented Generation (RAG) architecture.

LLMs are responsible only for

• semantic understanding

• natural language generation

Everything else must be deterministic Python.

The objective is maximum correctness, explainability, reliability, and testability.

------------------------------------------------------------

COMPLETE PIPELINE

Incoming User History
(messages[])

↓

LLM Call #1

Conversation State Extraction

↓

ConversationState

↓

Rule-Based Router

↓

Choose exactly one route

• Clarify

• Recommend

• Refine

• Compare

• Refuse

↓

IF ROUTE = Compare

↓

Comparison Pipeline

↓

Assessment Records

↓

Prompt Builder

↓

LLM Call #2

↓

Validator

↓

Response Builder

↓

Final JSON

------------------------------------------------------------

IF ROUTE = Recommend OR Refine

↓

Query Builder

↓

Hybrid Retrieval

↓

BM25 Retrieval

+

Embedding Retrieval

↓

Reciprocal Rank Fusion (RRF)

↓

Confidence Gate

↓

Top 5–8 Assessment Records

↓

Prompt Builder

↓

LLM Call #2

↓

Validator

↓

Response Builder

↓

Final JSON

------------------------------------------------------------

IF ROUTE = Clarify

↓

Prompt Builder

↓

LLM Call #2

↓

Final JSON

------------------------------------------------------------

IF ROUTE = Refuse

↓

Prompt Builder

↓

LLM Call #2

↓

Final JSON

------------------------------------------------------------

COMPONENT RESPONSIBILITIES

LLM #1

Only extracts structured conversation information.

It never

• retrieves

• recommends

• ranks

• compares

• generates metadata

Output

ConversationState

------------------------------------------------------------

ConversationState

Represents the complete structured understanding of the conversation.

Future modules may extend this model only if approved.

------------------------------------------------------------

Rule-Based Router

Pure Python.

Never use an LLM.

Responsibilities

• determine intent

• choose conversation route

• decide whether clarification is required

• decide recommend vs refine

• handle scope decisions

------------------------------------------------------------

Comparison Pipeline

Uses catalog records only.

No retrieval.

Assessment lookup

↓

Exact match

↓

RapidFuzz fallback

↓

Catalog records

------------------------------------------------------------

Query Builder

Pure Python.

Converts ConversationState into an optimized retrieval query.

Uses

• role

• seniority

• skills

• constraints

• static query expansion rules

Never uses an LLM.

------------------------------------------------------------

Hybrid Retrieval

Runs two retrieval strategies

BM25

Sentence Embeddings

Returns

Top 20 candidates from each.

------------------------------------------------------------

RRF Fusion

Merge

BM25

Embedding

↓

Single ranked list.

Use standard Reciprocal Rank Fusion.

Do not manually tune ranking weights.

------------------------------------------------------------

Confidence Gate

Determines whether retrieval confidence is sufficient.

If confidence is low,

override recommendation

↓

clarification.

This prevents weak recommendations.

------------------------------------------------------------

Prompt Builder

Constructs the prompt for LLM #2.

Provides

• conversation history

• router decision

• top 5–8 catalog records only

Never include the full catalog.

------------------------------------------------------------

LLM #2

Only responsible for generating conversational output.

Returns

{
    "reply": "...",
    "recommended_names": [...],
    "end_of_conversation": true|false
}

It never returns

• URLs

• test_type

• descriptions

• metadata

• recommendation objects

------------------------------------------------------------

Validator

Pure Python.

Responsibilities

Resolve recommended_names

↓

Exact catalog lookup

↓

Discard unresolved names

↓

Validate recommendation count

↓

Validate schema

No fuzzy matching.

------------------------------------------------------------

Response Builder

Pure Python.

Builds the final API response.

Looks up

• URL

• test_type

• metadata

from the catalog.

The LLM never generates these fields.

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Maximum

Two LLM calls per request.

Never three.

Never one giant prompt.

Never multiple agents.

------------------------------------------------------------

SYSTEM PROPERTIES

The architecture must remain

• deterministic

• modular

• testable

• stateless

• explainable

• production ready

Each component must have exactly one responsibility.

No component should duplicate another component's work.

------------------------------------------------------------

IMPLEMENTATION PRINCIPLES

Every module should be independently testable.

Every module should expose clean interfaces.

No hidden dependencies.

No circular imports.

No implicit global state.

No persistent conversation memory.

Every request reconstructs state from the supplied conversation history.

------------------------------------------------------------

IMPORTANT

This prompt defines the architecture only.

It does not define implementation details.

It does not define technologies.

It does not define coding standards.

Future prompts will specify those separately.

Never redesign this architecture.
