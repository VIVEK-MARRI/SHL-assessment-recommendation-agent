ROLE

Continue following all previous prompts.

This is the FIRST implementation module.

Your responsibility is ONLY to initialize the project foundation.

Do NOT implement business logic.

Do NOT implement scraping.

Do NOT implement retrieval.

Do NOT implement FastAPI endpoints.

Do NOT implement any AI logic.

Your goal is to create a clean, production-ready repository structure that every future module will build upon.

------------------------------------------------------------

OBJECTIVE

Initialize the complete project skeleton.

This establishes

• folder structure

• configuration

• dependency management

• logging

• project initialization

• development tooling

No functional application logic should exist after this module.

------------------------------------------------------------

CREATE THE FOLLOWING STRUCTURE

project_root/

├── api/
│
├── agent/
│
├── catalog/
│
├── config/
│
├── eval/
│
├── models/
│
├── retrieval/
│
├── tests/
│
├── docs/
│
├── scripts/
│
├── logs/
│
├── .gitignore
├── .env.example
├── README.md
├── pyproject.toml
├── requirements.txt
├── config.py
└── main.py

------------------------------------------------------------

CONFIGURATION

Create a centralized configuration system.

Requirements

• environment variable loading

• typed configuration

• default values where appropriate

• validation of required variables

No module should read environment variables directly.

Everything should go through the configuration module.

------------------------------------------------------------

LOGGING

Create centralized logging configuration.

Requirements

• logging module

• console logging

• file logging

• log levels

• timestamp formatting

Future modules should import this logger.

Never use print().

------------------------------------------------------------

DEPENDENCIES

Create

requirements.txt

Include only the dependencies required for the current project architecture.

Do not include unnecessary libraries.

Group dependencies logically.

------------------------------------------------------------

README

Create an initial README containing

Project overview

Architecture summary

Folder structure

Installation

Development setup

Running locally

Future modules

Do not document features that are not yet implemented.

------------------------------------------------------------

GITIGNORE

Generate a production-ready .gitignore.

Include

Python

Virtual environments

IDE files

Logs

Model caches

Environment variables

FAISS indexes

Temporary files

------------------------------------------------------------

ENVIRONMENT TEMPLATE

Generate

.env.example

Include every environment variable expected by future modules.

Use placeholder values.

Never include real secrets.

------------------------------------------------------------

CODE QUALITY

Every file must be production quality.

No placeholders.

No TODO comments.

No incomplete functions.

------------------------------------------------------------

OUTPUT FORMAT

Provide

1.

Repository structure

2.

Complete source code

3.

Explanation of every created file

4.

How to run the project foundation

5.

Verification checklist

Do not continue to scraper implementation.

Stop after the repository foundation is complete.

------------------------------------------------------------

IMPORTANT

This module establishes the foundation for every future module.

Do not implement any business logic.

Do not scrape the catalog.

Do not create FastAPI endpoints.

Do not create retrieval indexes.

Do not implement ConversationState.

Do not implement AI functionality.

Only build the project foundation.
