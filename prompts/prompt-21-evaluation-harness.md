ROLE

Continue following ALL previous prompts without exception.

This is Implementation Module 21.

Implement ONLY the Evaluation Harness.

Do NOT modify any runtime modules.

Do NOT modify FastAPI.

Do NOT modify Retrieval.

Do NOT modify Prompt Builder.

Do NOT modify Validation.

Do NOT modify Response Builder.

Do NOT modify LLM Generation.

Do NOT modify Router.

Do NOT modify Query Builder.

Do NOT modify Comparison Pipeline.

Do NOT modify Conversation State Extraction.

The Evaluation Harness must NEVER affect production execution.

------------------------------------------------------------

OBJECTIVE

Build a complete offline evaluation framework for the SHL Assessment Recommendation Agent.

The framework measures retrieval quality, routing accuracy, state extraction accuracy, recommendation quality, latency, and regression stability.

It is completely isolated from runtime inference.

------------------------------------------------------------

FOLDER STRUCTURE

evaluation/

__init__.py

metrics.py

retrieval_evaluator.py

router_evaluator.py

state_evaluator.py

recommendation_evaluator.py

benchmark.py

report_generator.py

datasets/

retrieval_eval.json

routing_eval.json

conversation_eval.json

recommendation_eval.json

reports/

scripts/

run_evaluation.py

tests/evaluation/

test_metrics.py

test_retrieval_evaluator.py

test_router_evaluator.py

test_state_evaluator.py

test_recommendation_evaluator.py

------------------------------------------------------------

DO NOT

Modify production indexes

Modify catalog

Modify API

Modify runtime pipeline

Perform training

Perform fine tuning

------------------------------------------------------------

RETRIEVAL EVALUATION

Evaluate

Embedding Retrieval

BM25 Retrieval

Hybrid Retrieval

Metrics

Recall@1

Recall@3

Recall@5

Recall@10

MRR

NDCG

Precision@K

Average latency

------------------------------------------------------------

ROUTER EVALUATION

Evaluate

Predicted Route

vs

Expected Route

Metrics

Accuracy

Precision

Recall

F1

Confusion Matrix

------------------------------------------------------------

STATE EXTRACTION

Evaluate

Extracted ConversationState

vs

Expected State

Metrics

Field Accuracy

JSON Validity

Extraction Latency

Retry Rate

------------------------------------------------------------

RECOMMENDATION EVALUATION

Evaluate

Generated recommendations

vs

Expected assessments

Metrics

Exact Match

Top-3 Accuracy

Top-5 Accuracy

Recommendation Precision

Recommendation Recall

Average Recommendation Count

------------------------------------------------------------

BENCHMARK

Create

benchmark.py

Measure

End-to-end latency

Retrieval latency

Embedding latency

BM25 latency

Hybrid latency

Prompt build latency

Generation latency

Validation latency

Response build latency

Average

Median

P95

P99

------------------------------------------------------------

METRICS

Implement

Recall@K

MRR

NDCG

Precision@K

Accuracy

Precision

Recall

F1

Latency statistics

Use deterministic implementations.

No sklearn metric helpers.

------------------------------------------------------------

REPORT GENERATOR

Generate

Markdown report

JSON report

Summary table

Charts optional

Report location

evaluation/reports/

------------------------------------------------------------

DATASETS

Use JSON files only.

Never hardcode examples.

Support

Retrieval dataset

Routing dataset

Conversation dataset

Recommendation dataset

------------------------------------------------------------

CLI

Create

scripts/run_evaluation.py

Support

--retrieval

--routing

--state

--recommendation

--benchmark

--all

Outputs

Console summary

Markdown report

JSON report

------------------------------------------------------------

LOGGING

logging.getLogger(__name__)

Log

Dataset size

Metrics

Latency

Failures

Report path

------------------------------------------------------------

UNIT TESTS

Create

tests/evaluation/

Cover

Metric correctness

Recall calculations

MRR

NDCG

Precision@K

Router accuracy

Recommendation evaluator

Benchmark calculations

Report generation

Dataset loading

------------------------------------------------------------

SUCCESS CRITERIA

Module 21 is complete only if

✓ No runtime modules modified

✓ Offline evaluation only

✓ Retrieval metrics implemented

✓ Router metrics implemented

✓ Recommendation metrics implemented

✓ Benchmark implemented

✓ Markdown reports generated

✓ JSON reports generated

✓ CLI works

✓ All tests pass

Stop after implementing ONLY the Evaluation Harness.

Do NOT modify runtime code.

Do NOT implement Docker.

Do NOT implement deployment.
