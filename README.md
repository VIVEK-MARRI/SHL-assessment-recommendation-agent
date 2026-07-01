# SHL Assessment Recommendation Agent

Production-grade backend foundation for a deterministic Retrieval-Augmented Generation (RAG) system that recommends SHL Individual Test Solutions through conversational interaction.

This repository currently contains only project foundation and development infrastructure.

## Current Status

Implemented in this module:

- Repository structure and package boundaries
- Centralized typed configuration
- Centralized logging setup (console + file)
- Dependency management and tooling configuration
- Minimal startup bootstrap

Not implemented yet:

- Catalog ingestion and validation logic
- Retrieval and ranking logic
- Agent routing logic
- LLM integration logic
- API endpoints

## Architecture Summary

The target architecture is a deterministic, modular pipeline with exactly two LLM calls per request:

1. Conversation state extraction (LLM #1)
2. Response generation from curated context (LLM #2)

All retrieval, validation, routing, and response assembly components are deterministic Python modules.

## Repository Structure

```
.
├── api/            # API layer package (no endpoints yet)
├── agent/          # Agent orchestration package
├── catalog/        # Catalog data and catalog-related modules
├── config/         # Configuration and logging modules
├── eval/           # Evaluation package
├── models/         # Typed data models
├── retrieval/      # Retrieval and ranking modules
├── tests/          # Unit and integration tests
├── docs/           # Project documentation
├── scripts/        # Utility and operational scripts
├── logs/           # Runtime logs
├── .env.example
├── .gitignore
├── config.py       # Backward-compatible config export
├── main.py         # Foundation bootstrap entrypoint
├── pyproject.toml
└── requirements.txt
```

## Installation

1. Create a Python 3.11 virtual environment.
2. Install dependencies.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Development Setup

1. Copy the environment template and set local values.

```bash
copy .env.example .env
```

2. Validate toolchain setup.

```bash
ruff check .
mypy .
pytest
```

## Running Locally

Run foundation bootstrap:

```bash
python main.py
```

Expected behavior:

- Loads typed settings from environment
- Initializes central logger
- Logs startup configuration summary (non-sensitive)
- Exits successfully

## Future Modules

Planned implementation phases will add:

1. Catalog pipeline and validation
2. Conversation state model and extractor
3. Deterministic router and route handlers
4. Hybrid retrieval (BM25 + embedding + RRF)
5. Validation and response builder
6. API endpoints and integration tests

Each phase will preserve the locked architecture and engineering standards.