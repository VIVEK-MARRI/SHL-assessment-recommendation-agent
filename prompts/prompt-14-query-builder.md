ROLE

Continue following ALL previous prompts.

This is a small architectural refinement before Module 14.

Do NOT redesign the Router.

Do NOT change routing behavior.

Do NOT change routing priority.

Do NOT modify tests except where necessary.

This task only extends the RoutingDecision model to improve downstream orchestration.

------------------------------------------------------------

OBJECTIVE

The Rule-Based Router currently decides what action should be taken.

Before implementing Module 14 (Query Builder), extend the RoutingDecision model so downstream orchestration becomes completely deterministic.

This is an architectural improvement only.

No routing logic should change.

------------------------------------------------------------

MODIFICATIONS

Update

agent/routing_models.py

Extend

RoutingDecision

with ONE additional field.

Option A (preferred)

next_module: Literal[
    "query_builder",
    "comparison_pipeline",
    "clarification",
    "refusal"
]

OR

Option B

query_strategy: Literal[
    "recommend",
    "refine",
    "compare",
    "clarify",
    "refuse"
]

Prefer Option A.

------------------------------------------------------------

ROUTER MAPPING

REFUSE

↓

next_module = "refusal"

CLARIFY

↓

next_module = "clarification"

COMPARE

↓

next_module = "comparison_pipeline"

RECOMMEND

↓

next_module = "query_builder"

REFINE

↓

next_module = "query_builder"

------------------------------------------------------------

IMPORTANT

Do NOT change

route

reason

confidence

clarification_field

comparison_required

query_required

recommendation_required

Only extend the model.

------------------------------------------------------------

TESTS

Update

tests/agent/test_router.py

Verify

REFUSE maps correctly

CLARIFY maps correctly

COMPARE maps correctly

RECOMMEND maps correctly

REFINE maps correctly

Existing routing behavior must remain unchanged.

------------------------------------------------------------

CLI

Update

scripts/test_router.py

Display

Route

Next Module

Confidence

Reason

------------------------------------------------------------

CONSTRAINTS

No new routing logic.

No new dependencies.

No retrieval.

No LLM.

No Prompt Builder.

No Query Builder.

No FastAPI.

------------------------------------------------------------

SUCCESS

The Router should produce output similar to

{
  "route": "RECOMMEND",
  "next_module": "query_builder",
  "confidence": "HIGH",
  "reason": "...",
  ...
}

Stop after completing this small architectural enhancement.

<ADDITIONAL_METADATA>
The current local time is: 2026-07-01T16:00:35+05:30.

The user's current state is as follows:
Active Document: c:\vivek\SHL-assessment-recommendation-agent\scripts\generate_catalog.py (LANGUAGE_PYTHON)
Cursor is on line: 1
Other open documents:
- c:\vivek\SHL-assessment-recommendation-agent\catalog\constants.py (LANGUAGE_PYTHON)
- c:\vivek\SHL-assessment-recommendation-agent\prompts\prompt-00-project-context.md (LANGUAGE_MARKDOWN)
- c:\vivek\SHL-assessment-recommendation-agent\scripts\generate_catalog.py (LANGUAGE_PYTHON)
- c:\vivek\SHL-assessment-recommendation-agent\catalog\raw_catalog.json (LANGUAGE_JSON)
- c:\vivek\SHL-assessment-recommendation-agent\agent\__init__.py (LANGUAGE_PYTHON)
</ADDITIONAL_METADATA>