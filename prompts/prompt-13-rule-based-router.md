ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 13.

Implement ONLY the Rule-Based Router.

Do NOT implement Query Builder.

Do NOT implement Prompt Builder.

Do NOT implement LLM Response Generation.

Do NOT implement Retrieval.

Do NOT implement FastAPI.

Do NOT implement Validation.

Do NOT implement Conversation State Extraction.

This module must be entirely deterministic.

No LLM calls are allowed.

------------------------------------------------------------

OBJECTIVE

The Router receives a validated ConversationState and deterministically decides what the system should do next.

The Router NEVER answers the user.

The Router NEVER retrieves assessments.

The Router ONLY decides the next action.

------------------------------------------------------------

INPUT

ConversationState

(from Module 12)

------------------------------------------------------------

OUTPUT

RoutingDecision

------------------------------------------------------------

FOLDER STRUCTURE

agent/

router.py

routing_models.py

tests/agent/

test_router.py

scripts/

test_router.py

------------------------------------------------------------

ROUTING DECISIONS

Implement

RouteType

Enum

REFUSE

CLARIFY

COMPARE

RECOMMEND

REFINE

------------------------------------------------------------

RoutingDecision

Fields

route

reason

confidence

clarification_field

query_required

comparison_required

recommendation_required

------------------------------------------------------------

ROUTING ORDER

The router must follow this exact priority.

Step 1

If

scope_flag

!=

"in_scope"

↓

REFUSE

------------------------------------------------------------

Step 2

If

comparison_requested

== True

AND

mentioned_assessment_names

contains at least one assessment

↓

COMPARE

------------------------------------------------------------

Step 3

If

clarification_needed

== True

↓

CLARIFY

------------------------------------------------------------

Step 4

If

ConversationState contains enough information for retrieval

↓

RECOMMEND

------------------------------------------------------------

Step 5

If

ConversationState indicates updated requirements

↓

REFINE

------------------------------------------------------------

No other routing paths are allowed.

------------------------------------------------------------

CLARIFICATION PRIORITY

When clarification is required

Ask for only ONE missing item.

Priority

1.

role

2.

seniority

3.

technical_skills

4.

leadership_required

5.

personality_required

6.

cognitive_required

7.

simulation_required

8.

constraints

Return

clarification_field

Example

"technical_skills"

------------------------------------------------------------

SUFFICIENT INFORMATION

Recommend only when

role exists

AND

technical_skills not empty

Seniority optional.

------------------------------------------------------------

REFINE

Detect

added constraints

removed skills

changed duration

changed requirement

added simulations

removed personality

added leadership

Return

REFINE

------------------------------------------------------------

ROUTER CONFIDENCE

Return

HIGH

MEDIUM

LOW

Examples

HIGH

Enough information

MEDIUM

Needs clarification

LOW

Off topic

------------------------------------------------------------

IMPLEMENTATION

Pure Python

No LLM

No Prompts

No Retrieval

No Catalog

No FastAPI

------------------------------------------------------------

ERRORS

Create

RoutingError

InvalidConversationState

Never use generic exceptions.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Input state

Selected route

Reason

Latency

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_router.py

Cover

Refuse

Compare

Clarify

Recommend

Refine

Priority order

Clarification priority

Missing role

Missing skills

Prompt injection

Off-topic

------------------------------------------------------------

CLI

Create

scripts/test_router.py

Input

ConversationState JSON

Output

RoutingDecision

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Router knows NOTHING about

Catalog

Retrieval

Hybrid Search

Prompt Builder

LLMs

FastAPI

Validator

Response Builder

Recommendations

It ONLY decides

What happens next.

------------------------------------------------------------

SUCCESS CRITERIA

Module 13 is complete only if

✓ Pure deterministic Python

✓ No LLM

✓ Correct routing priority

✓ Clarification priority implemented

✓ Refuse path implemented

✓ Compare path implemented

✓ Recommend path implemented

✓ Refine path implemented

✓ CLI works

✓ Tests pass

Stop after implementing ONLY the Rule-Based Router.
