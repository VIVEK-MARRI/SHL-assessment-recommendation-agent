ROLE

Continue following all instructions from:

• Prompt 00 — Project Context
• Prompt 01 — Catalog Context
• Prompt 02 — Conversation Behavior
• Prompt 03 — Locked Architecture

This prompt defines the engineering standards that every module in this project must follow.

These standards are mandatory.

Never violate them unless explicitly instructed.

------------------------------------------------------------

ENGINEERING PHILOSOPHY

This project is a production-quality backend system.

Write code that is:

• maintainable

• modular

• deterministic

• testable

• scalable

• easy to review

Optimize for engineering quality rather than writing the shortest code.

Never sacrifice readability for fewer lines of code.

------------------------------------------------------------

PYTHON VERSION

Target Python 3.11.

Use modern Python features where appropriate.

------------------------------------------------------------

GENERAL CODING PRINCIPLES

Follow

• SOLID Principles

• DRY (Don't Repeat Yourself)

• KISS (Keep It Simple)

• Single Responsibility Principle

Each module should have one responsibility.

Each function should perform one task.

Never write large monolithic functions.

------------------------------------------------------------

TYPE SAFETY

Every public function must include complete type hints.

Every variable with non-obvious types should be typed.

Avoid Any whenever possible.

Prefer explicit models.

------------------------------------------------------------

PYDANTIC

Use Pydantic v2.

All request and response objects should be strongly typed.

Validation should happen through models rather than manual dictionary checks.

------------------------------------------------------------

ERROR HANDLING

Never use

except:

Always catch specific exceptions.

Every external dependency must have graceful failure handling.

Examples

• HTTP requests

• LLM API calls

• file reading

• JSON parsing

• embedding loading

• index loading

Failures should never expose internal stack traces to API users.

------------------------------------------------------------

LOGGING

Never use

print()

Use the Python logging module.

Logging should include

• startup events

• retrieval events

• validation failures

• API errors

• warnings

Avoid logging sensitive data.

------------------------------------------------------------

CONFIGURATION

All configuration must come from a central config module.

Never hardcode

• API keys

• model names

• file paths

• ports

• environment-specific settings

Use environment variables.

Provide sensible defaults where appropriate.

------------------------------------------------------------

PROJECT STRUCTURE

Maintain a clean package structure.

Separate

• models

• retrieval

• agent

• API

• evaluation

• configuration

• tests

Never place unrelated logic in the same module.

------------------------------------------------------------

DEPENDENCY MANAGEMENT

Once a library is selected for a subsystem,

do not replace it later without approval.

Example

SentenceTransformers

↓

Always SentenceTransformers

FastAPI

↓

Always FastAPI

RapidFuzz

↓

Always RapidFuzz

Avoid unnecessary dependencies.

------------------------------------------------------------

DOCUMENTATION

Every module must begin with a module docstring describing its responsibility.

Every public class must have a class docstring.

Every public function must include

Args

Returns

Raises (when appropriate)

Use Google-style docstrings.

------------------------------------------------------------

TESTABILITY

Every module must be independently testable.

Avoid hidden global state.

Avoid circular imports.

Avoid side effects during import.

Use dependency injection where appropriate.

------------------------------------------------------------

PERFORMANCE

Initialize expensive resources once.

Examples

• embedding model

• FAISS index

• BM25 index

Do not reload resources on every request.

Minimize unnecessary LLM calls.

Avoid redundant catalog loading.

------------------------------------------------------------

SECURITY

Never expose

• API keys

• internal exceptions

• file system paths

Validate all external inputs.

Treat all user input as untrusted.

------------------------------------------------------------

API DESIGN

The API layer must remain thin.

Business logic belongs in service modules.

FastAPI endpoints should only

• validate requests

• call services

• return responses

Never implement business logic inside API routes.

------------------------------------------------------------

CODE STYLE

Follow PEP8.

Use meaningful names.

Avoid abbreviations unless universally understood.

Prefer explicit code over clever code.

Favor readability over compactness.

------------------------------------------------------------

QUALITY CHECKLIST

Before considering any module complete, verify that it satisfies all of the following:

✓ Single responsibility

✓ Fully typed

✓ Documented

✓ Logged appropriately

✓ Unit-testable

✓ No hardcoded values

✓ No placeholder code

✓ Proper exception handling

✓ Clean interfaces

✓ Compatible with the locked architecture

------------------------------------------------------------

IMPORTANT

This prompt defines engineering standards only.

It does not define business logic.

It does not define retrieval.

It does not define prompting.

It does not define architecture.

Every future module must follow these standards consistently.

If implementing a requested module requires changing another module or violating these standards, stop and explain why before making any changes.
