# Final Evaluation Report

## Executive Summary

Automated official-style evaluation completed against deterministic SHL scoring checks.

## Metrics

- Hard Evaluation Pass Rate: 1.0000
- Mean Recall@10: 1.0000
- Precision@1: 0.8750
- Precision@3: 0.5833
- Precision@5: 0.4500
- Behavior Probe Pass Rate: 1.0000
- Average Retrieval Latency: 26.98 ms
- Average Conversation Turns: 1.67
- Estimated SHL Evaluation Score: 1.0000

## Failure Analysis

- No failures detected by the automated harness.

## Regression Summary

The harness validates schema, route behavior, catalog grounding, turn caps, and Recall@10-oriented recommendation ordering.

## Remaining Risks

- Hidden SHL cases may use labels or assessment aliases not represented in the local evaluation datasets.
- LLM-dependent state extraction and natural-language response wording still depend on provider availability and output quality.
