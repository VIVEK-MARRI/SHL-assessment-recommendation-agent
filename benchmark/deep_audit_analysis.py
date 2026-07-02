#!/usr/bin/env python3
"""Deep audit analysis of SHL assessment recommendation system."""

import json
import os
import traceback
import math
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_FILE = os.path.join(BASE, "catalog", "catalog.json")
FULL_COV_FILE = os.path.join(BASE, "benchmark", "audit_full_catalog_coverage.json")
STRESS_AUDIT_FILE = os.path.join(BASE, "benchmark", "audit_unseen_stress_test.json")
STRESS_BENCH_FILE = os.path.join(BASE, "benchmark", "stress_benchmark.json")
REPORTS_DIR = os.path.join(BASE, "benchmark", "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

OUTPUT_LINES = []
def p(*args, **kwargs):
    line = " ".join(str(a) for a in args)
    OUTPUT_LINES.append(line)
    print(*args, **kwargs)

def flush_output(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(OUTPUT_LINES))
    p(f"\n--- Full output saved to {path} ---")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

p("=" * 80)
p("DEEP AUDIT ANALYSIS -- SHL Assessment Recommendation Agent")
p("=" * 80)

try:
    catalog = load_json(CATALOG_FILE)
    p(f"\nLoaded catalog: {len(catalog)} assessments")
except Exception as e:
    traceback.print_exc()
    catalog = []
    p(f"ERROR loading catalog: {e}")

try:
    full_cov = load_json(FULL_COV_FILE)
    p(f"Loaded full coverage audit: {full_cov['summary']['num_queries']} queries")
except Exception as e:
    traceback.print_exc()
    full_cov = {"summary": {}, "cat_summary": {}, "results": []}
    p(f"ERROR loading full coverage: {e}")

try:
    stress_audit = load_json(STRESS_AUDIT_FILE)
    p(f"Loaded stress audit: {stress_audit['summary']['num_queries']} queries")
except Exception as e:
    traceback.print_exc()
    stress_audit = {"summary": {}, "cat_summary": {}, "results": []}
    p(f"ERROR loading stress audit: {e}")

try:
    stress_bench = load_json(STRESS_BENCH_FILE)
    p(f"Loaded stress benchmark: {len(stress_bench)} query entries")
except Exception as e:
    traceback.print_exc()
    stress_bench = []
    p(f"ERROR loading stress benchmark: {e}")

# Build catalog index
cat_by_id = {a["entity_id"]: a for a in catalog}
all_cat_ids = set(cat_by_id.keys())

# Build stress benchmark map: query text -> entry
stress_bench_map = {q["query"]: q for q in stress_bench}

# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------
def safe_div(a, b):
    return a / b if b else 0.0

def compute_metrics(retrieved_ids, relevant_ids):
    """Compute precision@k, recall@10, mrr, ndcg@10 given retrieved and relevant id lists."""
    p1 = 1.0 if len(retrieved_ids) > 0 and retrieved_ids[0] in relevant_ids else 0.0
    p3 = sum(1 for rid in retrieved_ids[:3] if rid in relevant_ids) / 3.0 if len(retrieved_ids) >= 3 else 0.0
    p5 = sum(1 for rid in retrieved_ids[:5] if rid in relevant_ids) / 5.0 if len(retrieved_ids) >= 5 else 0.0
    p10 = sum(1 for rid in retrieved_ids[:10] if rid in relevant_ids) / 10.0
    r10 = sum(1 for rid in retrieved_ids[:10] if rid in relevant_ids) / len(relevant_ids) if relevant_ids else 0.0
    # MRR
    mrr = 0.0
    first_rank = None
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            mrr = 1.0 / (i + 1)
            first_rank = i + 1
            break
    # nDCG@10
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids[:10]):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant_ids), 10)))
    ndcg = dcg / idcg if idcg > 0 else 0.0
    return {
        "p@1": p1, "p@3": p3, "p@5": p5, "p@10": p10,
        "r@10": r10, "mrr": mrr, "ndcg@10": ndcg, "first_relevant_rank": first_rank
    }


# ===================================================================
# ANALYSIS 1: NEVER-RETRIEVED ASSESSMENTS (stress benchmark)
# ===================================================================
def analysis_1_never_retrieved():
    p("\n" + "=" * 80)
    p("ANALYSIS 1: NEVER-RETRIEVED ASSESSMENTS (from stress audit)")
    p("=" * 80)
    try:
        seen_ids = set()
        retrieved_detail = {}  # entity_id -> list of (query, rank, score)
        for r in stress_audit.get("results", []):
            for item in r.get("retrieved", []):
                eid = item["entity_id"]
                seen_ids.add(eid)
                if eid not in retrieved_detail:
                    retrieved_detail[eid] = []
                retrieved_detail[eid].append({
                    "query": r["query"],
                    "category": r.get("category", ""),
                    "rank": item["rank"],
                    "score": item["score"]
                })

        never_retrieved = all_cat_ids - seen_ids
        never_retrieved_sorted = sorted(never_retrieved, key=lambda x: cat_by_id.get(x, {}).get("name", ""))

        p(f"\nTotal catalog: {len(all_cat_ids)}")
        p(f"Seen in stress audit: {len(seen_ids)}")
        p(f"Never retrieved: {len(never_retrieved)}")

        report_lines = [
            "# Failure Analysis: Never-Retrieved Assessments (Stress Benchmark)",
            f"\n- **Total catalog assessments**: {len(all_cat_ids)}",
            f"- **Assessments retrieved at least once**: {len(seen_ids)}",
            f"- **Never retrieved (any query)**: {len(never_retrieved)}",
            f"- **Coverage**: {len(seen_ids) / len(all_cat_ids) * 100:.1f}%\n",
        ]

        if not never_retrieved:
            p("\n[GOOD] Every assessment was retrieved at least once in the stress audit!")
            report_lines.append("\n**Every assessment was retrieved at least once.**")
        else:
            p(f"\n--- Details for each never-retrieved assessment ---\n")
            for eid in never_retrieved_sorted:
                a = cat_by_id.get(eid, {})
                name = a.get("name", "N/A")
                keys = ", ".join(a.get("keys", []))
                job_levels = ", ".join(a.get("job_levels", []))
                languages = ", ".join(a.get("languages", []))
                duration = a.get("duration", "N/A")
                description = a.get("description", "")[:200]

                p(f"\n  [{eid}] {name}")
                p(f"  Keys: {keys}")
                p(f"  Job Levels: {job_levels}")
                p(f"  Languages: {languages}")
                p(f"  Duration: {duration}")
                p(f"  Description: {description}")

                # Find top-5 queries from stress_benchmark that this would be relevant for
                relevant_queries = []
                for q in stress_bench:
                    if eid in q.get("relevant_ids", []):
                        relevant_queries.append(q)
                relevant_queries = relevant_queries[:5]

                if relevant_queries:
                    p(f"  Top queries it WOULD be relevant for:")
                    for q in relevant_queries:
                        p(f"    - \"{q['query']}\" (cat: {q['category']}, form: {q['formulation']})")
                else:
                    p(f"  No stress benchmark queries list this as relevant.")

                # Analyze niche assessment
                desc_lower = description.lower()
                name_lower = name.lower()
                niche_indicators = []
                if len(a.get("keys", [])) == 1 and a["keys"][0] in ("Knowledge & Skills",):
                    niche_indicators.append("single knowledge/skills key (generic)")
                if a.get("duration", "").replace(" minutes", "").isdigit():
                    mins = int(a.get("duration", "0").replace(" minutes", ""))
                    if mins <= 5:
                        niche_indicators.append(f"short duration ({mins} min)")
                is_niche = len(niche_indicators) > 0
                p(f"  Niche indicators: {niche_indicators if niche_indicators else 'None apparent'}")
                p(f"  Assessment appears {'niche' if is_niche else 'general'}")

                report_lines.append(f"\n---\n### [{eid}] {name}")
                report_lines.append(f"- **Keys**: {keys}")
                report_lines.append(f"- **Job Levels**: {job_levels}")
                report_lines.append(f"- **Languages**: {languages}")
                report_lines.append(f"- **Duration**: {duration}")
                report_lines.append(f"- **Description**: {description}")
                if relevant_queries:
                    report_lines.append(f"- **Relevant for these stress queries**:")
                    for q in relevant_queries:
                        report_lines.append(f"  - \"{q['query']}\" ({q['category']})")
                else:
                    report_lines.append(f"- **No stress query lists this as relevant**")
                report_lines.append(f"- **Niche analysis**: {niche_indicators if niche_indicators else 'Not obviously niche'}")

        md_path = os.path.join(REPORTS_DIR, "failure_analysis.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        p(f"\nReport saved to {md_path}")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_1_never_retrieved: {e}")


# ===================================================================
# ANALYSIS 2: FALSE POSITIVE PATTERNS (stress benchmark)
# ===================================================================
def analysis_2_false_positives():
    p("\n" + "=" * 80)
    p("ANALYSIS 2: FALSE POSITIVE PATTERNS -- Over-Retrieved Irrelevant Assessments")
    p("=" * 80)
    try:
        # Count how many times each assessment is retrieved but NOT relevant
        false_pos_counts = Counter()  # entity_id -> count of irrelevant retrievals
        total_retrievals = Counter()  # entity_id -> total retrievals
        false_pos_by_cat = defaultdict(Counter)  # category -> entity_id -> count

        for r in stress_audit.get("results", []):
            query = r["query"]
            category = r.get("category", "unknown")
            stress_entry = stress_bench_map.get(query, {})
            relevant_ids = set(stress_entry.get("relevant_ids", []))
            for item in r.get("retrieved", []):
                eid = item["entity_id"]
                total_retrievals[eid] += 1
                if eid not in relevant_ids:
                    false_pos_counts[eid] += 1
                    false_pos_by_cat[category][eid] += 1

        # Top-20 over-retrieved
        top20_fp = false_pos_counts.most_common(20)

        p(f"\nTop-20 Most Frequently Retrieved Irrelevant Assessments (False Positives)\n")
        p(f"{'Rank':<5} {'ID':<8} {'Name':<45} {'FP Count':<10} {'Total Ret':<10} {'FP Rate':<10} {'Keys'}")
        p("-" * 130)
        report_lines = [
            "# False Positive Pattern Analysis (Stress Benchmark)",
            "\n## Top-20 Over-Retrieved Assessments (Irrelevant Retrievals)\n",
            "| Rank | ID | Name | False Positive Count | Total Retrievals | FP Rate | Keys | Categories Appearing |",
            "|------|----|------|---------------------|-----------------|---------|------|---------------------|",
        ]

        for rank, (eid, fp_count) in enumerate(top20_fp, 1):
            a = cat_by_id.get(eid, {})
            name = a.get("name", "N/A")[:42]
            total = total_retrievals[eid]
            fp_rate = fp_count / total * 100 if total else 0
            keys = ", ".join(a.get("keys", []))[:50]

            # Categories where this is a false positive
            cats_where_fp = {}
            for cat, counter in false_pos_by_cat.items():
                if eid in counter:
                    cats_where_fp[cat] = counter[eid]
            cats_str = ", ".join(sorted(cats_where_fp.keys()))[:50]

            p(f"{rank:<5} {eid:<8} {name:<45} {fp_count:<10} {total:<10} {fp_rate:<10.1f}% {keys}")
            report_lines.append(
                f"| {rank} | {eid} | {name} | {fp_count} | {total} | {fp_rate:.1f}% | {keys} | {cats_str} |"
            )

        # Analyze dominance
        p(f"\n--- Cross-category analysis of top false positives ---")
        report_lines.append("\n## Cross-Category FP Analysis\n")
        for rank, (eid, fp_count) in enumerate(top20_fp, 1):
            a = cat_by_id.get(eid, {})
            name = a.get("name", "N/A")
            cats = dict(false_pos_by_cat.get(next((c for c in false_pos_by_cat if eid in false_pos_by_cat[c]), ""), {}))
            # Actually let me aggregate properly
            relevant_cats = {}
            for cat, counter in false_pos_by_cat.items():
                if eid in counter:
                    relevant_cats[cat] = counter[eid]
            p(f"\n  [{eid}] {name}")
            p(f"  Appears as false positive in categories: {dict(relevant_cats)}")
            report_lines.append(f"\n- **[{eid}] {name}**: FP across categories: {dict(relevant_cats)}")

        md_path = os.path.join(REPORTS_DIR, "false_positives.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        p(f"\nReport saved to {md_path}")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_2_false_positives: {e}")


# ===================================================================
# ANALYSIS 3: CATEGORY PERFORMANCE (both benchmarks)
# ===================================================================
def analysis_3_category_performance():
    p("\n" + "=" * 80)
    p("ANALYSIS 3: PER-CATEGORY PERFORMANCE (Both Benchmarks)")
    p("=" * 80)
    try:
        for label, audit_data, bench_data, source_label in [
            ("FULL CATALOG COVERAGE", full_cov, None, "full_coverage"),
            ("UNSEEN STRESS TEST", stress_audit, stress_bench, "stress_test"),
        ]:
            p(f"\n{'-' * 60}")
            p(f"  {label}")
            p(f"{'-' * 60}")
            cat_sum = audit_data.get("cat_summary", {})

            # Sort by p@1 ascending (worst first)
            sorted_cats = sorted(cat_sum.items(), key=lambda x: x[1].get("precision@1", 1))

            p(f"\n{'Category':<30} {'Count':<8} {'P@1':<8} {'P@3':<8} {'P@5':<8} {'P@10':<8} {'R@10':<8} {'MRR':<8} {'nDCG@10':<8}")
            p("-" * 100)
            for cat, s in sorted_cats:
                p(f"{cat:<30} {s.get('count',0):<8} {s.get('precision@1',0):<8.4f} {s.get('precision@3',0):<8.4f} "
                  f"{s.get('precision@5',0):<8.4f} {s.get('precision@10',0):<8.4f} {s.get('recall@10',0):<8.4f} "
                  f"{s.get('mrr',0):<8.4f} {s.get('ndcg@10',0):<8.4f}")

            # Identify worst categories
            worst_cats = [c for c, s in sorted_cats[:5] if s.get("count", 0) >= 3]
            p(f"\n--- Worst performing categories (count>=3, lowest P@1) ---")
            for cat in worst_cats:
                s = cat_sum[cat]
                p(f"\n  Category: {cat} (count={s.get('count',0)}, P@1={s.get('precision@1',0):.4f})")

                # Find sample queries in this category
                sample_results = [r for r in audit_data.get("results", []) if r.get("category", "") == cat]
                sample_results = sample_results[:3]
                for sr in sample_results:
                    retrieved_names = []
                    for item in sr.get("retrieved", [])[:5]:
                        a = cat_by_id.get(item["entity_id"], {})
                        retrieved_names.append(f"{item['entity_id']}/{a.get('name','?')}")
                    p(f"    Query: \"{sr['query']}\"")
                    p(f"      First rel rank: {sr.get('first_relevant_rank', 'None')}")
                    p(f"      Top-5: {', '.join(retrieved_names)}")

        # Build and save report
        report_lines = [
            "# Per-Category Performance Analysis\n",
            "## Full Catalog Coverage\n",
            "| Category | Count | P@1 | P@3 | P@5 | P@10 | R@10 | MRR | nDCG@10 |",
            "|----------|-------|-----|-----|-----|------|------|-----|---------|",
        ]
        for cat, s in sorted(full_cov.get("cat_summary", {}).items(), key=lambda x: x[1].get("precision@1", 1)):
            report_lines.append(
                f"| {cat} | {s.get('count',0)} | {s.get('precision@1',0):.4f} | {s.get('precision@3',0):.4f} | "
                f"{s.get('precision@5',0):.4f} | {s.get('precision@10',0):.4f} | {s.get('recall@10',0):.4f} | "
                f"{s.get('mrr',0):.4f} | {s.get('ndcg@10',0):.4f} |"
            )

        report_lines.extend([
            "\n## Unseen Stress Test\n",
            "| Category | Count | P@1 | P@3 | P@5 | P@10 | R@10 | MRR | nDCG@10 |",
            "|----------|-------|-----|-----|-----|------|------|-----|---------|",
        ])
        for cat, s in sorted(stress_audit.get("cat_summary", {}).items(), key=lambda x: x[1].get("precision@1", 1)):
            report_lines.append(
                f"| {cat} | {s.get('count',0)} | {s.get('precision@1',0):.4f} | {s.get('precision@3',0):.4f} | "
                f"{s.get('precision@5',0):.4f} | {s.get('precision@10',0):.4f} | {s.get('recall@10',0):.4f} | "
                f"{s.get('mrr',0):.4f} | {s.get('ndcg@10',0):.4f} |"
            )

        md_path = os.path.join(REPORTS_DIR, "category_analysis.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        p(f"\nReport saved to {md_path}")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_3_category_performance: {e}")


# ===================================================================
# ANALYSIS 4: RANK DISTRIBUTION
# ===================================================================
def analysis_4_rank_distribution():
    p("\n" + "=" * 80)
    p("ANALYSIS 4: RANK DISTRIBUTION -- Where does first relevant result appear?")
    p("=" * 80)
    try:
        for label, audit_data in [
            ("FULL CATALOG COVERAGE", full_cov),
            ("UNSEEN STRESS TEST", stress_audit),
        ]:
            p(f"\n{'-' * 50}")
            p(f"  {label}")
            p(f"{'-' * 50}")

            ranks = []
            queries_not_top5 = []
            queries_not_top10 = []
            for r in audit_data.get("results", []):
                fr = r.get("first_relevant_rank")
                if fr is not None:
                    ranks.append(fr)
                    if fr > 5:
                        queries_not_top5.append((r["query"], fr))
                    if fr > 10:
                        queries_not_top10.append((r["query"], fr))
                else:
                    # No relevant found at all
                    pass

            # Histogram
            hist = {
                "1": sum(1 for r in ranks if r == 1),
                "2-3": sum(1 for r in ranks if 2 <= r <= 3),
                "4-5": sum(1 for r in ranks if 4 <= r <= 5),
                "6-10": sum(1 for r in ranks if 6 <= r <= 10),
                "11-20": sum(1 for r in ranks if 11 <= r <= 20),
                ">20": sum(1 for r in ranks if r > 20),
            }
            total_queries_with_relevant = len(ranks)

            p(f"\n  Distribution of first-relevant rank:")
            p(f"  {'Bucket':<10} {'Count':<8} {'%':<8}")
            p(f"  {'-' * 26}")
            for bucket, cnt in hist.items():
                pct = cnt / total_queries_with_relevant * 100 if total_queries_with_relevant else 0
                p(f"  {bucket:<10} {cnt:<8} {pct:<8.2f}%")
            p(f"\n  Total queries with relevant found: {total_queries_with_relevant}")

            p(f"\n  Queries where first relevant is NOT in top-5:")
            for qtext, r in queries_not_top5[:10]:
                p(f"    Rank {r:>3}: \"{qtext}\"")
            if len(queries_not_top5) > 10:
                p(f"    ... and {len(queries_not_top5) - 10} more")

            p(f"\n  Queries where first relevant is NOT in top-10:")
            for qtext, r in queries_not_top10[:10]:
                p(f"    Rank {r:>3}: \"{qtext}\"")
            if len(queries_not_top10) > 10:
                p(f"    ... and {len(queries_not_top10) - 10} more")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_4_rank_distribution: {e}")


# ===================================================================
# ANALYSIS 5: LATENCY ANALYSIS
# ===================================================================
def analysis_5_latency():
    p("\n" + "=" * 80)
    p("ANALYSIS 5: LATENCY ANALYSIS")
    p("=" * 80)
    try:
        for label, audit_data in [
            ("FULL CATALOG COVERAGE", full_cov),
            ("UNSEEN STRESS TEST", stress_audit),
        ]:
            p(f"\n{'-' * 50}")
            p(f"  {label}")
            p(f"{'-' * 50}")

            latencies = []
            for r in audit_data.get("results", []):
                if "latency_ms" in r:
                    latencies.append(r["latency_ms"])

            if not latencies:
                p("  No per-query latency data available in this audit file.")
                # Try summary
                s = audit_data.get("summary", {})
                for key in ["avg_latency_ms", "p95_latency_ms", "p99_latency_ms"]:
                    if key in s:
                        p(f"  {key}: {s[key]:.2f} ms (from summary)")
                continue

            latencies.sort()
            n = len(latencies)
            p50 = latencies[int(n * 0.5)]
            p95 = latencies[int(n * 0.95)]
            p99 = latencies[int(n * 0.99)]
            pmax = latencies[-1]
            pavg = sum(latencies) / n

            p(f"\n  Latency statistics (ms):")
            p(f"    Avg:  {pavg:.2f}")
            p(f"    P50:  {p50:.2f}")
            p(f"    P95:  {p95:.2f}")
            p(f"    P99:  {p99:.2f}")
            p(f"    Max:  {pmax:.2f}")
            p(f"    Samples: {n}")

            # Slowest 10 queries
            sorted_by_latency = sorted(
                [r for r in audit_data.get("results", []) if "latency_ms" in r],
                key=lambda x: x["latency_ms"], reverse=True
            )[:10]
            p(f"\n  Slowest 10 queries:")
            for i, r in enumerate(sorted_by_latency, 1):
                p(f"    {i:>2}. {r['latency_ms']:>8.2f} ms -- \"{r['query'][:80]}\" (cat: {r.get('category','?')})")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_5_latency: {e}")


# ===================================================================
# ANALYSIS 6: ASSESSMENTS WITH NO TEXTUAL OVERLAP
# ===================================================================
def analysis_6_no_textual_overlap():
    p("\n" + "=" * 80)
    p("ANALYSIS 6: TEXTUAL OVERLAP -- Can simple queries find each assessment?")
    p("=" * 80)
    try:
        stress_results = stress_audit.get("results", [])
        # Build for each assessment: which queries retrieved it and with what scores
        assessment_retrieval_map = defaultdict(list)
        for r in stress_results:
            for item in r.get("retrieved", []):
                eid = item["entity_id"]
                assessment_retrieval_map[eid].append({
                    "query": r["query"],
                    "category": r.get("category", ""),
                    "rank": item["rank"],
                    "score": item["score"]
                })

        # Pick a sample of assessments that were never or rarely retrieved
        retrieval_counts = {eid: len(v) for eid, v in assessment_retrieval_map.items()}
        never_or_rare = sorted(
            [eid for eid in all_cat_ids if retrieval_counts.get(eid, 0) <= 1],
            key=lambda x: retrieval_counts.get(x, 0)
        )[:30]

        p(f"\nAssessments that were retrieved 0-1 times in stress audit: {len(never_or_rare)} found")
        p(f"Analyzing first {len(never_or_rare)}:\n")

        for eid in never_or_rare:
            a = cat_by_id.get(eid, {})
            if not a:
                continue
            name = a.get("name", "")
            desc = a.get("description", "")
            keys = a.get("keys", [])
            duration = a.get("duration", "")

            p(f"\n  [{eid}] {name}")
            p(f"  Description: {desc[:150]}")
            p(f"  Keys: {keys}")
            ret_count = retrieval_counts.get(eid, 0)
            p(f"  Times retrieved: {ret_count}")

            # Generate 3 simple recruiter queries
            # Use name words, key concepts from description
            words = name.replace("(New)", "").replace("(new)", "").strip()
            # Take first meaningful part of name
            name_parts = [w for w in words.split() if len(w) > 2 and w not in ["New", "new"]]

            # Pick description keywords
            desc_words = desc.replace("-", " ").replace(",", "").split()
            key_terms = [w for w in desc_words if len(w) > 4][:5]

            queries = []
            if name_parts:
                queries.append(" ".join(name_parts[:4]))
            if len(name_parts) > 2:
                queries.append("need someone skilled in " + " ".join(name_parts[:3]).lower())
            if key_terms:
                queries.append("experience with " + " and ".join(key_terms[:3]).lower())

            queries = queries[:3]
            while len(queries) < 3:
                queries.append(f"looking for {name.lower()}")
                break

            p(f"  Generated queries:")
            for qi, qtext in enumerate(queries):
                p(f"    Q{qi+1}: \"{qtext}\"")

                # Find matching entries in stress_bench
                matched_stress = [q for q in stress_bench if eid in q.get("relevant_ids", [])]
                if matched_stress:
                    matching_query = matched_stress[0]["query"]
                    p(f"      -> Stress benchmark knows it as relevant for: \"{matching_query}\"")

                    # Check if any audit result for that query actually retrieved it
                    found_in_audit = False
                    for r in stress_results:
                        if r["query"] == matching_query:
                            retrieved_ids = [x["entity_id"] for x in r.get("retrieved", [])]
                            if eid in retrieved_ids:
                                found_rank = [x["rank"] for x in r.get("retrieved", []) if x["entity_id"] == eid][0]
                                found_score = [x["score"] for x in r.get("retrieved", []) if x["entity_id"] == eid][0]
                                p(f"      -> Audit found it at rank {found_rank} (score {found_score:.4f})")
                                found_in_audit = True
                                break
                    if not found_in_audit:
                        p(f"      -> Audit did NOT retrieve it for this query!")
                else:
                    p(f"      -> No stress benchmark query lists this as relevant.")

            # Diagnose why it might not be found
            issues = []
            # Check if name is too generic
            common_words = ["test", "assessment", "solution", "report", "survey", "scale", "profile", "questionnaire"]
            word_matches = sum(1 for w in common_words if w in name.lower())
            if word_matches >= 2:
                issues.append("name may be too generic")

            # Check if keys are minimal
            if len(keys) <= 1:
                issues.append("single classification key")

            # Check duration
            if duration:
                try:
                    mins = int(duration.replace(" minutes", ""))
                    if mins <= 5:
                        issues.append(f"very short ({mins} min)")
                except:
                    pass

            # Check description length
            if len(desc) < 50:
                issues.append("very short description")
            elif len(desc) < 100:
                issues.append("short description")

            if issues:
                p(f"  Diagnosis: {', '.join(issues)}")
            else:
                p(f"  Diagnosis: No obvious issues detected")

    except Exception as e:
        traceback.print_exc()
        p(f"ERROR in analysis_6_no_textual_overlap: {e}")


# ===================================================================
# RUN ALL
# ===================================================================
if __name__ == "__main__":
    analysis_1_never_retrieved()
    analysis_2_false_positives()
    analysis_3_category_performance()
    analysis_4_rank_distribution()
    analysis_5_latency()
    analysis_6_no_textual_overlap()

    p("\n" + "=" * 80)
    p("DEEP AUDIT ANALYSIS COMPLETE")
    p("=" * 80)

    flush_output(os.path.join(BASE, "benchmark", "deep_audit_output.txt"))
