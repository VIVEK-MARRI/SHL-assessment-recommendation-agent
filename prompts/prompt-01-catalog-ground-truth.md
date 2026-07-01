ROLE

Continue using all instructions from Prompt 00 (Project Context).

This prompt establishes the SHL Individual Test Solutions catalog as the single source of truth for the entire system.

Never override these rules in future modules.

------------------------------------------------------------

CATALOG IS THE GROUND TRUTH

The SHL Individual Test Solutions catalog is the only authoritative source for assessment information.

If no exact catalog record exists, the recommendation must be discarded.

Never guess.

Never substitute.

Every recommendation, comparison, explanation, and metadata lookup must originate from this catalog.

Never use pretrained model knowledge to invent or supplement catalog information.

If the catalog does not contain an assessment, state that clearly.

Never hallucinate missing assessments.

------------------------------------------------------------

CATALOG SCHEMA

Every assessment record follows this structure.

Assessment

- entity_id
- name
- link
- description
- keys
- job_levels
- job_levels_raw
- languages
- languages_raw
- duration
- duration_raw
- status
- remote
- adaptive

These fields define the complete knowledge available to the system.

No additional metadata should ever be invented.

------------------------------------------------------------

SINGLE SOURCE OF TRUTH

The catalog is authoritative for:

• assessment names

• URLs

• descriptions

• duration

• supported languages

• adaptive status

• remote testing availability

• job levels

• assessment categories

No other source may override catalog information.

------------------------------------------------------------

DATA QUALITY RULES

The catalog may contain malformed or inconsistent data.

Future modules must assume the catalog has already passed through a cleaning and validation pipeline.

Cleaning includes:

• removing duplicate whitespace

• removing embedded newlines

• trimming strings

• validating URLs

• normalizing booleans

• removing duplicate records

• logging malformed entries

Downstream modules must never attempt to "fix" catalog data.

They should trust the validated catalog.

------------------------------------------------------------

ASSESSMENT SCOPE

Only SHL Individual Test Solutions are valid.

Never recommend Job Solutions.

Never retrieve Job Solutions.

Never compare Job Solutions.

Never expose Job Solutions in recommendations.

------------------------------------------------------------

ASSESSMENT MATCHING

Assessment identity is determined by its canonical catalog name.

Future retrieval modules may use semantic similarity.

Future comparison modules may use fuzzy matching.

However, final recommendation validation must always resolve to an exact catalog record.

If no exact catalog record exists, the recommendation must be discarded.

Never guess.

Never substitute.

------------------------------------------------------------

CATALOG LIMITATIONS

The catalog is intentionally limited.

Some requested technologies, roles, or assessments may not exist.

When this occurs:

• acknowledge the limitation

• explain that the catalog has no direct assessment

• recommend the closest supported alternatives

Never fabricate missing assessments.

------------------------------------------------------------

TEST TYPE MAPPING

The final API requires a test_type field.

This field is derived deterministically from the assessment's keys field.

The mapping is fixed.

Knowledge & Skills                 → K

Personality & Behavior             → P

Ability & Aptitude                 → A

Competencies                       → C

Biodata & Situational Judgment     → B

Simulations                        → S

Development & 360                  → D

Assessment Exercises               → E

If an assessment belongs to multiple categories,
combine the codes in catalog order.

Example

["Knowledge & Skills", "Simulations"]

↓

"K,S"

This mapping is deterministic.

LLMs must never generate test_type values.

------------------------------------------------------------

RECOMMENDATION PRINCIPLES

Every recommendation must satisfy all of the following:

✓ exists in catalog

✓ canonical assessment name

✓ canonical URL

✓ metadata derived from catalog

✓ grounded explanation

Recommendations must never be based on assumptions.

------------------------------------------------------------

IMPORTANT

This prompt defines the catalog rules only.

It does not define architecture.

It does not define retrieval.

It does not define prompting.

It does not define implementation.

Every future module must treat the validated SHL catalog as the only source of truth.
