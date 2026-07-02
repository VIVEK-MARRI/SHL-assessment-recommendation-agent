# SHL Assessment Retrieval Audit Report
## Executive Summary
This report presents a comprehensive audit of the SHL assessment retrieval system across two benchmarks: a **Full Catalog Coverage** set (2262 queries) that tests whether every assessment in the catalog can be retrieved by at least one formulation, and an **Unseen Stress Test** set (1119 queries) that evaluates generalization to unseen, real-world query patterns.
The full-coverage benchmark achieves 84.4% Precision@1 and 99.7% Recall@10, with 100% catalog coverage and average latency of 49.8ms. This confirms that every assessment in the 377-item catalog can be successfully retrieved by at least one query formulation.
The unseen stress benchmark shows a significant drop: Precision@1 of 46.0% and Recall@10 of 22.5%, with 95.8% of assessments ever retrieved. This gap between seen and unseen performance highlights the challenge of generalizing from curated queries to noisy, real-world inputs. Key recommendations include improving handling of idiomatic and abbreviation-heavy queries, expanding synonym coverage, and adding robustness to mixed-case and missing-punctuation inputs.
## Benchmark Overview
| Metric | Full Coverage (2262 queries) | Unseen Stress (1119 queries) |
|--------|:---:|:---:|
| Precision@1 | 0.8439 | 0.4602 |
| Precision@3 | 0.3236 | 0.3983 |
| Precision@5 | 0.1984 | 0.3651 |
| Precision@10 | 0.0997 | 0.3132 |
| Recall@10 | 0.9973 | 0.2248 |
| MRR | 0.9083 | 0.6084 |
| nDCG@10 | 0.9083 | 0.3793 |
| Avg Latency (ms) | 49.7760 | 26.5935 |
| P95 Latency (ms) | 81.9637 | 37.9238 |
| Coverage | 100.0% | 95.8% |
| Never Retrieved | 0 | 16 |

## 1. Full Catalog Coverage Assessment
### 1.1 Overall Performance
The full catalog coverage benchmark evaluates 2262 queries designed to retrieve every assessment in the 377-item SHL catalog. The system achieves:

- **100% catalog coverage** — every assessment is retrieved by at least one query formulation.
- **Precision@1 of 84.4%** — for 84.4% of queries, the top result is the target assessment.
- **Recall@10 of 99.7%** — for 99.7% of queries, the target assessment appears within the top 10.
- **MRR of 0.9083** — the average reciprocal rank indicates the target is typically ranked first.
- **Average latency of 49.8ms** with P95 at 82.0ms.

A small number of queries (approximately 6) fail to return the target within the top 10, primarily in the cognitive and competencies categories.
### 1.2 Rank Distribution
The table below shows where the first relevant assessment appears in the ranked results:

| First Relevant Rank | Count | Percentage |
|:---:|:---:|:---:|
| 1 | 1909 | 84.4% |
| 2-3 | 287 | 12.7% |
| 4-5 | 48 | 2.1% |
| 6-10 | 12 | 0.5% |
| 11-20 | 1 | 0.0% |
| not found | 5 | 0.2% |

### 1.3 Category Breakdown
Categories sorted by worst Precision@1:

| Category | Count | P@1 | P@3 | Recall@10 | MRR |
|----------|:-----:|:---:|:---:|:---------:|:---:|
| situational_judgment | 60 | 60.0% | 30.6% | 100.0% | 0.7589 |
| competencies | 30 | 63.3% | 33.3% | 100.0% | 0.7833 |
| personality | 360 | 63.6% | 30.5% | 98.6% | 0.7800 |
| simulation | 210 | 67.1% | 31.6% | 99.5% | 0.8101 |
| development | 30 | 70.0% | 31.1% | 100.0% | 0.8167 |
| cognitive | 192 | 71.4% | 30.4% | 100.0% | 0.8204 |
| testing | 36 | 77.8% | 33.3% | 100.0% | 0.8889 |
| exercises | 6 | 83.3% | 33.3% | 100.0% | 0.9167 |
| sql | 66 | 84.8% | 33.3% | 100.0% | 0.9217 |
| java | 54 | 87.0% | 33.3% | 100.0% | 0.9352 |
| general | 696 | 96.6% | 33.3% | 100.0% | 0.9825 |
| software_engineering | 234 | 98.3% | 33.3% | 100.0% | 0.9915 |
| backend | 30 | 100.0% | 33.3% | 100.0% | 1.0000 |
| cloud | 12 | 100.0% | 33.3% | 100.0% | 1.0000 |
| cybersecurity | 12 | 100.0% | 33.3% | 100.0% | 1.0000 |
| dotnet | 60 | 100.0% | 33.3% | 100.0% | 1.0000 |
| engineering | 42 | 100.0% | 33.3% | 100.0% | 1.0000 |
| finance | 18 | 100.0% | 33.3% | 100.0% | 1.0000 |
| frontend | 48 | 100.0% | 33.3% | 100.0% | 1.0000 |
| hr | 18 | 100.0% | 33.3% | 100.0% | 1.0000 |
| leadership | 6 | 100.0% | 33.3% | 100.0% | 1.0000 |
| marketing | 18 | 100.0% | 33.3% | 100.0% | 1.0000 |
| mobile | 12 | 100.0% | 33.3% | 100.0% | 1.0000 |
| python | 6 | 100.0% | 33.3% | 100.0% | 1.0000 |
| sales | 6 | 100.0% | 33.3% | 100.0% | 1.0000 |

### 1.4 Formulation Performance
Performance grouped by query formulation type:

| Formulation | Count | P@1 | P@3 | Recall@10 | MRR |
|-------------|:-----:|:---:|:---:|:---------:|:---:|
| direct | 377 | 93.6% | 33.1% | 100.0% | 0.9645 |
| recruiter | 377 | 79.6% | 31.8% | 99.7% | 0.8759 |
| role | 377 | 86.2% | 32.5% | 99.7% | 0.9200 |
| scenario | 377 | 85.7% | 32.7% | 99.7% | 0.9206 |
| short | 377 | 79.8% | 32.0% | 99.7% | 0.8805 |
| skill | 377 | 81.4% | 32.0% | 99.5% | 0.8884 |

## 2. Unseen Query Generalization
### 2.1 Overall Performance
The unseen stress benchmark evaluates 1119 queries that simulate real-world user inputs, including typos, abbreviations, jargon, conversational phrasing, and mixed casing. Key findings:

- **Precision@1 of 46.0%** — less than half of queries get the correct assessment at rank 1.
- **Recall@10 of 22.5%** — only 22.5% of relevant assessments appear in the top 10 on average.
- **MRR of 0.6084** — the correct assessment is often ranked lower than in the coverage benchmark.
- **Coverage of 95.8%** — 16 assessments were never retrieved by any unseen query.
- **Average latency of 26.6ms** — faster than the coverage benchmark due to simpler queries.

The significant drop from the coverage benchmark is expected — the stress test is designed to probe edge cases where query phrasing diverges from catalog names.
### 2.2 Formulation Type Performance
The stress benchmark uses diverse formulation types to simulate real-world variability:

| Formulation | Count | P@1 | P@3 | Recall@10 | MRR |
|-------------|:-----:|:---:|:---:|:---------:|:---:|
| abbreviation | 73 | 19.2% | 14.2% | 86.8% | 0.2422 |
| conversational | 104 | 27.9% | 26.6% | 14.5% | 0.4754 |
| idiomatic | 55 | 21.8% | 24.2% | 12.8% | 0.4334 |
| jargon | 82 | 47.6% | 39.4% | 14.5% | 0.6243 |
| long_messy | 175 | 21.7% | 26.3% | 15.4% | 0.4757 |
| missing_punctuation | 79 | 40.5% | 32.1% | 13.2% | 0.5462 |
| mixed_caps | 60 | 55.0% | 47.8% | 19.8% | 0.7056 |
| partial_requirement | 79 | 69.6% | 52.7% | 24.6% | 0.7732 |
| range | 60 | 73.3% | 68.3% | 24.3% | 0.8290 |
| role_skill_comb | 217 | 61.3% | 50.7% | 18.1% | 0.7313 |
| short | 135 | 63.7% | 51.4% | 23.3% | 0.7435 |

### 2.3 Category Breakdown (Stress)
Categories sorted by worst Recall@10:

| Category | Count | P@1 | Recall@10 | MRR | nDCG@10 |
|----------|:-----:|:---:|:---------:|:---:|:-------:|
| assessment_exercises | 5 | 20.0% | 11.0% | 0.4400 | 0.2135 |
| development_360 | 67 | 25.4% | 12.3% | 0.4410 | 0.2424 |
| marketing | 14 | 64.3% | 12.5% | 0.7172 | 0.3658 |
| biodata_situational_judgment | 29 | 24.1% | 13.8% | 0.4971 | 0.2881 |
| simulations | 16 | 62.5% | 14.4% | 0.6541 | 0.4262 |
| entry_level | 1 | 0.0% | 15.0% | 0.1667 | 0.1337 |
| personality | 1 | 0.0% | 15.0% | 0.2500 | 0.1622 |
| devops | 80 | 48.8% | 15.2% | 0.6647 | 0.3766 |
| backend | 64 | 53.1% | 15.6% | 0.6639 | 0.3685 |
| python | 37 | 48.6% | 15.8% | 0.6369 | 0.3729 |
| management | 87 | 39.1% | 16.0% | 0.5801 | 0.3427 |
| finance | 4 | 75.0% | 16.2% | 0.8750 | 0.4838 |
| cybersecurity | 41 | 48.8% | 17.0% | 0.6396 | 0.4005 |
| ability_aptitude | 33 | 30.3% | 17.6% | 0.5217 | 0.3371 |
| data_science | 77 | 67.5% | 18.0% | 0.7762 | 0.4965 |
| customer_service | 10 | 90.0% | 18.4% | 0.9125 | 0.4959 |
| mobile | 14 | 64.3% | 19.1% | 0.7649 | 0.4484 |
| frontend | 67 | 50.7% | 19.2% | 0.6467 | 0.3947 |
| cognitive | 16 | 12.5% | 19.7% | 0.4583 | 0.3234 |
| testing | 39 | 30.8% | 20.6% | 0.4978 | 0.2889 |
| cloud | 69 | 52.2% | 21.9% | 0.6492 | 0.3781 |
| personality_behavior | 70 | 28.6% | 24.1% | 0.4965 | 0.3296 |
| knowledge_skills | 120 | 64.2% | 24.4% | 0.7526 | 0.4841 |
| java | 44 | 43.2% | 26.3% | 0.6007 | 0.4813 |
| sql | 33 | 63.6% | 28.4% | 0.7213 | 0.5632 |
| sales | 20 | 75.0% | 29.8% | 0.8462 | 0.6543 |
| hr | 17 | 41.2% | 31.3% | 0.5980 | 0.4179 |
| general | 44 | 0.0% | 98.1% | 0.0038 | 0.0030 |

### 2.4 Never-Retrieved Assessments
Out of 377 total assessments, **16 assessments** were never retrieved in any of the 1119 unseen stress queries:

| entity_id | Name |
|-----------|------|
| 17 | Written English v1 |
| 3778 | Adobe Photoshop CC |
| 3994 | MS Word (New) |
| 3998 | Pediatrics (New) |
| 4044 | Ceramic Engineering (New) |
| 4048 | General Diseases (New) |
| 4058 | Medical Terminology (New) |
| 4095 | Prism (New) |
| 4096 | Molecular Biology (New) |
| 4107 | Paint Technology (New) |
| 4111 | Pharmaceutics (New) |
| 4114 | Pharmaceutical Chemistry (New) |
| 4115 | Apache Pig (New) |
| 4154 | Organic Chemistry (New) |
| 4161 | Biochemistry (New) |
| 4162 | Dermatology (New) |

## 3. False Positive Analysis
### 3.1 Overall FP Rates
Each query has exactly 1 relevant assessment out of 377 (rising to ~20 for personality/behavior queries). A random retriever would produce a false positive in 99.7% of all retrieved slots (since only 1 in 377 assessments is relevant). The actual FP rates are:

- **Coverage benchmark FP rate:** 95.0% (of 45,240 retrieved slots)
- **Stress benchmark FP rate:** 73.8% (of 22,380 retrieved slots)

The high FP rates are a direct consequence of the retrieval task design: with 377 candidate assessments and only 1 relevant per query, even an excellent retriever will show high FP counts. What matters is whether the relevant assessment appears in the top 10 — which it does in 99.7% of coverage queries and 22.5% of stress queries.
### 3.2 Most Over-Retrieved Assessments
Assessments that appear most frequently in retrieved results while rarely being the relevant target (from stress benchmark — top 10):

| entity_id | Name | Non-Relevant Retrievals | Total Retrievals |
|-----------|------|:----------------------:|:----------------:|
| 3976 | Verify Interactive G+ Candidate Report | 290 | 290 |
| 4130 | Salesforce Development (New) | 268 | 281 |
| 4019 | Adobe Experience Manager (New) | 250 | 274 |
| 382 | Following Instructions v1 - UK (R1) | 203 | 225 |
| 4062 | Drupal (New) | 202 | 213 |
| 4080 | HTML/CSS (New) | 187 | 188 |
| 4040 | ITIL (IT Infrastructure Library) (New) | 184 | 193 |
| 4171 | Search Engine Optimization (New) | 180 | 182 |
| 4116 | Operations Management (New) | 176 | 223 |
| 3941 | Verify - Following Instructions | 174 | 174 |

## 4. Category-Level Performance
### 4.1 Coverage Per Category
Comparing Precision@1 and Recall@10 across both benchmarks by category:

| Category | Cov Count | Cov P@1 | Cov R@10 | Str Count | Str P@1 | Str R@10 |
|----------|:---------:|:-------:|:--------:|:---------:|:-------:|:--------:|
| ability_aptitude | 0 | - | - | 33 | 30.3% | 17.6% |
| assessment_exercises | 0 | - | - | 5 | 20.0% | 11.0% |
| backend | 30 | 100.0% | 100.0% | 64 | 53.1% | 15.6% |
| biodata_situational_judgment | 0 | - | - | 29 | 24.1% | 13.8% |
| cloud | 12 | 100.0% | 100.0% | 69 | 52.2% | 21.9% |
| cognitive | 192 | 71.4% | 100.0% | 16 | 12.5% | 19.7% |
| competencies | 30 | 63.3% | 100.0% | 0 | - | - |
| customer_service | 0 | - | - | 10 | 90.0% | 18.4% |
| cybersecurity | 12 | 100.0% | 100.0% | 41 | 48.8% | 17.0% |
| data_science | 0 | - | - | 77 | 67.5% | 18.0% |
| development | 30 | 70.0% | 100.0% | 0 | - | - |
| development_360 | 0 | - | - | 67 | 25.4% | 12.3% |
| devops | 0 | - | - | 80 | 48.8% | 15.2% |
| dotnet | 60 | 100.0% | 100.0% | 0 | - | - |
| engineering | 42 | 100.0% | 100.0% | 0 | - | - |
| entry_level | 0 | - | - | 1 | 0.0% | 15.0% |
| exercises | 6 | 83.3% | 100.0% | 0 | - | - |
| finance | 18 | 100.0% | 100.0% | 4 | 75.0% | 16.2% |
| frontend | 48 | 100.0% | 100.0% | 67 | 50.7% | 19.2% |
| general | 696 | 96.6% | 100.0% | 44 | 0.0% | 98.1% |
| hr | 18 | 100.0% | 100.0% | 17 | 41.2% | 31.3% |
| java | 54 | 87.0% | 100.0% | 44 | 43.2% | 26.3% |
| knowledge_skills | 0 | - | - | 120 | 64.2% | 24.4% |
| leadership | 6 | 100.0% | 100.0% | 0 | - | - |
| management | 0 | - | - | 87 | 39.1% | 16.0% |
| marketing | 18 | 100.0% | 100.0% | 14 | 64.3% | 12.5% |
| mobile | 12 | 100.0% | 100.0% | 14 | 64.3% | 19.1% |
| personality | 360 | 63.6% | 98.6% | 1 | 0.0% | 15.0% |
| personality_behavior | 0 | - | - | 70 | 28.6% | 24.1% |
| python | 6 | 100.0% | 100.0% | 37 | 48.6% | 15.8% |
| sales | 6 | 100.0% | 100.0% | 20 | 75.0% | 29.8% |
| simulation | 210 | 67.1% | 99.5% | 0 | - | - |
| simulations | 0 | - | - | 16 | 62.5% | 14.4% |
| situational_judgment | 60 | 60.0% | 100.0% | 0 | - | - |
| software_engineering | 234 | 98.3% | 100.0% | 0 | - | - |
| sql | 66 | 84.8% | 100.0% | 33 | 63.6% | 28.4% |
| testing | 36 | 77.8% | 100.0% | 39 | 30.8% | 20.6% |

### 4.2 Weakest Categories
Categories with Precision@1 < 80% in the coverage benchmark or Recall@10 < 15% in the stress benchmark:

**Coverage benchmark — categories with P@1 < 0.8:**

| Category | P@1 | Recall@10 |
|----------|:---:|:---------:|
| cognitive | 71.4% | 100.0% |
| competencies | 63.3% | 100.0% |
| development | 70.0% | 100.0% |
| personality | 63.6% | 98.6% |
| simulation | 67.1% | 99.5% |
| situational_judgment | 60.0% | 100.0% |
| testing | 77.8% | 100.0% |

**Stress benchmark — categories with Recall@10 < 0.15:**

| Category | P@1 | Recall@10 |
|----------|:---:|:---------:|
| assessment_exercises | 20.0% | 11.0% |
| biodata_situational_judgment | 24.1% | 13.8% |
| development_360 | 25.4% | 12.3% |
| marketing | 64.3% | 12.5% |
| simulations | 62.5% | 14.4% |

## 5. Latency Analysis
### 5.1 Coverage Benchmark
| Metric | Value (ms) |
|--------|:----------:|
| Average | 49.78 |
| P50 | 46.18 |
| P95 | 81.96 |
| P99 | 168.87 |
| Max | 1444.97 |

### 5.2 Stress Benchmark
| Metric | Value (ms) |
|--------|:----------:|
| Average | 26.59 |
| P50 | 24.97 |
| P95 | 37.92 |
| P99 | 49.10 |
| Max | 78.60 |

## 6. Root Cause Analysis & Recommendations
### 6.1 What Works Well
- **100% catalog coverage** — all 377 assessments are retrievable by at least one formulation.
- **Excellent recall on direct queries** — Recall@10 of 99.7% on the full coverage benchmark.
- **Fast retrieval** — average latency of 50ms for coverage queries, 27ms for stress queries.
- **Strong P@1 on direct/skill/role formulations** — many categories achieve perfect P@1.
- **Every assessment is retrievable** — the never-retrieved list is empty for coverage, and only a small fraction are missed in stress.

### 6.2 What Needs Improvement
- **Cognitive and competencies categories lag in P@1** — categories like situational_judgment, competencies, personality have P@1 below 80% in coverage.
- **Unseen query generalization is weak** — P@1 drops from 84.4% to 46.0%. Worst-performing categories in stress: assessment_exercises, development_360, marketing.
- **Formulation sensitivity** — abbreviation (R@10=14.2%) and idiomatic (R@10=24.2%) and long_messy (R@10=26.3%) are the hardest formulation types.
- **Over-retrieval of popular assessments** — 'Verify Interactive G+ Candidate Report' is retrieved 290 times as a non-relevant result.
- **16 assessments never retrieved** in any unseen query — these may require dedicated query formulations or improved synonym coverage.

### 6.3 Recommendations
1. **Improve synonym expansion for cognitive/competency assessments** — these categories show the weakest P@1 in coverage. Adding domain-specific synonyms and paraphrases would help.
2. **Enhance handling of abbreviations and jargon** — create an abbreviation-to-full-name mapping and integrate it into the query preprocessing pipeline.
3. **Add robustness to casing and punctuation** — normalize mixed-case queries and expand contractions before retrieval.
4. **Tune retrieval for idiomatic/conversational queries** — these formulations show the largest P@1 drop. Consider fine-tuning embeddings on conversational data.
5. **Monitor over-retrieved assessments** — if certain assessments dominate results without being relevant, consider down-weighting them or adding negative feedback.
6. **Address never-retrieved assessments** — add explicit query formulations for each of the 16 assessments never retrieved in the stress test.

## 7. Conclusion
The SHL assessment retrieval system demonstrates strong performance on curated, direct queries: 100% catalog coverage, 84.4% Precision@1, and 99.7% Recall@10 in the full coverage benchmark. The system is fast, reliable, and ensures every assessment is discoverable.

However, the unseen stress benchmark reveals a substantial gap when generalizing to real-world query patterns: Precision@1 drops to 46.0% and Recall@10 to 22.5%. The primary failure modes are abbreviations, jargon, idiomatic phrasing, and casing variations. With targeted improvements to query preprocessing, synonym expansion, and embedding robustness, the system can significantly close this gap while maintaining its existing strengths.
