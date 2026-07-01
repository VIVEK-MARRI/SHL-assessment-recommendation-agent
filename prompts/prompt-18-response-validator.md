ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 18.

Implement ONLY the Response Validator.

Do NOT implement Response Builder.

Do NOT implement FastAPI.

Do NOT implement Retrieval.

Do NOT implement Prompt Builder.

Do NOT implement LLM Generation.

Do NOT implement Router.

Do NOT implement Query Builder.

Do NOT implement Comparison Pipeline.

Do NOT implement Conversation State Extraction.

This module is the final safety gate before any response reaches the user.

No LLM calls are allowed.

------------------------------------------------------------

OBJECTIVE

Validate the LLMGenerationResult produced by Module 17.

The validator trusts NOTHING from the LLM except that it attempted to return assessment names.

Every assessment name must be validated against the canonical catalog.

The validator NEVER performs retrieval.

The validator NEVER performs fuzzy matching.

The validator NEVER invents replacements.

------------------------------------------------------------

PIPELINE

LLMGenerationResult

↓

Validator

↓

ValidatedGenerationResult

↓

Module 19 (Response Builder)

------------------------------------------------------------

INPUT

LLMGenerationResult

------------------------------------------------------------

OUTPUT

ValidatedGenerationResult

Implement using Pydantic v2.

------------------------------------------------------------

FOLDER STRUCTURE

agent/

validator.py

validator_models.py

catalog_validator.py

tests/agent/

test_validator.py

test_catalog_validator.py

scripts/

test_validator.py

------------------------------------------------------------

LOAD CATALOG

Load ONLY

catalog/catalog.json

Never use

raw_catalog.json

Load once.

Cache in memory.

------------------------------------------------------------

VALIDATION MODEL

ValidatedGenerationResult

Fields

reply

validated_names

invalid_names

end_of_conversation

validation_passed

validation_errors

------------------------------------------------------------

VALIDATION RULES

Rule 1

reply

must not be empty

------------------------------------------------------------

Rule 2

recommended_names

must contain

0

or

1–10

items

Never allow

11+

------------------------------------------------------------

Rule 3

Every recommendation

must exist

in catalog.json

------------------------------------------------------------

Rule 4

Matching

Case-insensitive exact match only

Allowed

Example

OPQ32R

↓

OPQ32r

Not allowed

RapidFuzz

Embeddings

Levenshtein

Substring

------------------------------------------------------------

Rule 5

Duplicate assessment names

must be removed

Preserve original order.

------------------------------------------------------------

Rule 6

If a recommendation does not exist

Remove it.

Append it to

invalid_names

------------------------------------------------------------

Rule 7

If ALL recommendations are invalid

validated_names

must be empty

validation_passed

must be false

------------------------------------------------------------

Rule 8

If some recommendations are valid

Keep only valid ones.

validation_passed

true

------------------------------------------------------------

Rule 9

Never modify

reply

------------------------------------------------------------

IMPLEMENTATION

Pure deterministic Python.

No LLM.

No Retrieval.

No Prompt Builder.

No FastAPI.

------------------------------------------------------------

CATALOG VALIDATOR

Create

CatalogValidator

Methods

validate_name()

validate_names()

canonicalize_name()

------------------------------------------------------------

CATALOG CACHE

Load once.

Reuse.

Never reload per request.

------------------------------------------------------------

ERRORS

Create

ValidationError

CatalogValidationError

InvalidGenerationResult

CatalogLoadError

Never use generic exceptions.

------------------------------------------------------------

LOGGING

Use

logging.getLogger(__name__)

Log

Catalog loaded

Validated count

Rejected count

Rejected names

Latency

Never log prompts.

------------------------------------------------------------

UNIT TESTS

Create

tests/agent/

test_validator.py

test_catalog_validator.py

Cover

Empty reply

Valid recommendations

Mixed valid and invalid

All invalid

Duplicate recommendations

Case-insensitive exact match

Too many recommendations

Zero recommendations

Ordering preserved

Catalog cache

------------------------------------------------------------

CLI

Create

scripts/test_validator.py

Input

LLMGenerationResult JSON

Output

ValidatedGenerationResult

Latency

------------------------------------------------------------

ARCHITECTURAL CONSTRAINTS

Validator knows NOTHING about

Hybrid Retrieval

BM25

Embeddings

Prompt Builder

LLMs

FastAPI

Response Builder

It ONLY validates names against catalog.json.

------------------------------------------------------------

SUCCESS CRITERIA

Module 18 is complete only if

✓ Pure deterministic Python

✓ Loads only catalog.json

✓ Catalog cached

✓ Case-insensitive exact match only

✓ No fuzzy matching

✓ Duplicate removal

✓ Invalid names rejected

✓ Reply preserved

✓ CLI works

✓ Tests pass

Stop after implementing ONLY the Response Validator.

Do NOT implement Response Builder.

Do NOT inject URLs.

Do NOT inject metadata.

Do NOT build the final API response.
