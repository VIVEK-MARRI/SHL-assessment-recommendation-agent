ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 06.

Your responsibility is to build the Catalog Management Layer.

This module establishes the canonical SHL Individual Test Solutions catalog that every downstream component will consume.

Do NOT implement retrieval.

Do NOT implement FastAPI.

Do NOT implement ConversationState.

Do NOT implement routing.

Do NOT implement prompt engineering.

Do NOT implement any LLM integration.

Do NOT implement vector indexes.

Do NOT implement ranking.

The output of this module becomes the single source of truth for the entire system.

------------------------------------------------------------

OBJECTIVE

Build a production-grade catalog management layer responsible for

• loading

• validation

• normalization

• cleaning

• deduplication

• exporting

The runtime system must operate entirely from the validated catalog.

No downstream module should need additional preprocessing.

------------------------------------------------------------

INPUT

Assume a catalog file already exists.

The catalog represents the complete SHL Individual Test Solutions dataset.

The runtime system should never depend on downloading or scraping the website.

(Optional scraper utilities may exist later, but they are NOT part of this module.)

------------------------------------------------------------

OUTPUT

Produce a validated canonical catalog

catalog/catalog.json

Every downstream module must consume this file directly.

------------------------------------------------------------

CREATE THE FOLLOWING MODULES

catalog/

├── models.py
├── loader.py
├── cleaner.py
├── validator.py
├── normalizer.py
├── exporter.py
├── constants.py
├── catalog.json
└── __init__.py

------------------------------------------------------------

ASSESSMENT MODEL

Create a strongly typed Assessment model.

Fields

entity_id

name

link

description

keys

job_levels

job_levels_raw

languages

languages_raw

duration

duration_raw

status

remote

adaptive

Validation belongs inside the model whenever appropriate.

------------------------------------------------------------

LOADER

Responsibilities

Load catalog.json

Validate JSON structure

Instantiate Assessment objects

Raise informative exceptions

Never silently ignore malformed records.

------------------------------------------------------------

CLEANER

Implement deterministic cleaning.

Required rules

Trim whitespace

Collapse duplicate spaces

Remove embedded newlines

Normalize unicode

Remove invisible characters

Normalize URLs

Normalize boolean values

Normalize list formatting

Preserve semantic meaning

Cleaning must always produce identical output for identical input.

------------------------------------------------------------

NORMALIZER

Normalize

category names

language lists

job levels

status values

URL formatting

string casing where appropriate

No semantic transformations.

No guessing.

------------------------------------------------------------

VALIDATOR

Validate every assessment.

Required checks

entity_id exists

name exists

URL is valid

description exists

keys is a list

job_levels is a list

languages is a list

status exists

remote is bool

adaptive is bool

Reject malformed records.

Generate validation reports.

Log every failure.

Never silently discard data.

------------------------------------------------------------

DEDUPLICATION

Detect duplicates using

entity_id

canonical URL

Duplicate names

Duplicate URLs

Duplicate IDs

Never overwrite silently.

Log duplicate records.

------------------------------------------------------------

CONSTANTS

Create a constants module.

Move every reusable constant into this module.

Examples

Category names

Status values

Cleaning regex

URL prefixes

Boolean mappings

Key → test_type mapping

Never scatter constants across modules.

------------------------------------------------------------

KEY TO TEST_TYPE MAPPING

Implement a deterministic mapping.

Knowledge & Skills

↓

K

Personality & Behavior

↓

P

Ability & Aptitude

↓

A

Competencies

↓

C

Biodata & Situational Judgment

↓

B

Simulations

↓

S

Development & 360

↓

D

Assessment Exercises

↓

E

This mapping will be consumed later by the Response Builder.

Never generate these values using an LLM.

------------------------------------------------------------

EXPORTER

Export

catalog.json

Requirements

UTF-8

Pretty formatted

Stable ordering

Deterministic output

Repeatable builds

------------------------------------------------------------

LOGGING

Log

Catalog loading

Cleaning

Validation

Duplicates

Export completion

Record counts

Execution time

Never use print().

------------------------------------------------------------

ERROR HANDLING

Handle

Missing catalog

Malformed JSON

Invalid URLs

Validation failures

Encoding problems

Export failures

Raise meaningful exceptions.

Never expose internal stack traces.

------------------------------------------------------------

UNIT TESTS

Create unit tests for

Loader

Cleaner

Normalizer

Validator

Exporter

Assessment model

Duplicate detection

Malformed records

Missing fields

Invalid URLs

Whitespace normalization

Unicode normalization

Tests must be deterministic.

------------------------------------------------------------

OUTPUT QUALITY

Every module must

Use type hints

Use Google-style docstrings

Follow SOLID principles

Be independently testable

Contain no TODOs

Contain no placeholder code

Contain no dead code

------------------------------------------------------------

DELIVERABLES

Provide

1. Final folder structure

2. Complete production-ready source code

3. Explanation of every module

4. Sample validated catalog

5. Unit tests

6. Instructions for validating a new catalog

7. Verification checklist

Stop after the Catalog Management Layer is complete.

Do not implement retrieval.

Do not implement embeddings.

Do not implement BM25.

Do not implement FastAPI.

------------------------------------------------------------

SUCCESS CRITERIA

The module is complete only if

✓ Every catalog record loads successfully.

✓ Validation catches malformed data.

✓ Cleaning is deterministic.

✓ Duplicate detection works.

✓ Canonical catalog exports correctly.

✓ Unit tests pass.

✓ Downstream modules can consume catalog.json without additional preprocessing.

This module establishes the canonical knowledge base for the entire project.

Treat it as production data infrastructure.

Do not proceed to the next module.
