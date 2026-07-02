#!/usr/bin/env python3
"""Evaluation harness for the SHL Assessment Recommendation Agent.

Replays public conversation traces C1-C10 against the /chat API and
computes Recall@10, hallucination counts, and schema violation counts.

Usage:
    python eval/replay_harness.py [OPTIONS]

Options:
    --traces DIR      Path to directory containing C1.md-C10.md  [default: data/traces/]
    --server URL      Base URL for the API                        [default: http://localhost:8000]
    --output PATH     Path for the JSON report                    [default: eval/results/recall_report.json]
    --verbose         Print each turn's request and response
    --turn-delay SEC  Seconds to wait between turns              [default: 2.0]
    --trace-delay SEC Seconds to wait between traces             [default: 10.0]
    --retry-wait SEC  Base wait seconds on 429 before retry      [default: 35]
    --max-retries N   Max retries per turn on 429               [default: 3]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from typing import Optional
import requests


def post_with_retry(
    url: str,
    payload: dict,
    max_retries: int = 5,
    base_wait: int = 60,
    timeout: int = 90
) -> dict:
    """
    POST with exponential backoff on 429 and 503.
    Never raises on retriable errors — returns None after exhausting retries.
    Raises on 4xx client errors (bad schema, not our problem to retry).
    """
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                return resp.json()
            
            elif resp.status_code == 429:
                # Extract retry-after header if present
                retry_after = int(resp.headers.get("retry-after", base_wait))
                wait = max(retry_after, base_wait) * (2 ** attempt)
                print(f"  429 rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            
            elif resp.status_code == 503:
                wait = base_wait * (2 ** attempt)
                print(f"  503 server error — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            
            elif resp.status_code >= 400:
                print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
                return None  # Client error, don't retry
                
        except requests.Timeout:
            print(f"  Timeout on attempt {attempt+1}/{max_retries}")
            time.sleep(base_wait)
        except requests.ConnectionError as e:
            print(f"  Connection error: {e}")
            return None
    
    print(f"  EXHAUSTED {max_retries} retries — skipping this turn")
    return None


# ---------------------------------------------------------------------------
# Trace parser
# ---------------------------------------------------------------------------

def _extract_table_names(text: str) -> list:
    """Extract assessment names from markdown table rows (column 1 after #)."""
    names = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        num_cell = parts[1]
        name_cell = parts[2]
        if name_cell.lower() == "name" or "---" in name_cell:
            continue
        if not num_cell.isdigit():
            continue
        if name_cell:
            names.append(name_cell)
    return names


def _has_recommendation_table(text: str) -> bool:
    return bool(re.search(r"\|\s*#\s*\|\s*Name\s*\|", text))


def parse_trace(path: Path) -> dict:
    """Parse a conversation trace .md file."""
    content = path.read_text(encoding="utf-8")

    turn_pattern = re.compile(r"### Turn \d+", re.MULTILINE)
    sections = turn_pattern.split(content)[1:]  # skip preamble

    turns = []
    expected_names = []

    for section in sections:
        user_match = re.search(r"\*\*User\*\*\s*\n((?:>.*\n?)+)", section)
        agent_match = re.search(r"\*\*Agent\*\*\s*\n([\s\S]+?)(?=\*\*User\*\*|\Z)", section)

        user_content = None
        agent_content = None

        if user_match:
            raw_user = user_match.group(1)
            lines = []
            for line in raw_user.splitlines():
                stripped = line.strip()
                if stripped.startswith("> "):
                    lines.append(stripped[2:])
                elif stripped == ">":
                    lines.append("")
                else:
                    lines.append(stripped)
            user_content = "\n".join(lines).strip()

        if agent_match:
            agent_content = agent_match.group(1).strip()

        if user_content:
            turns.append({"role": "user", "content": user_content})

        if agent_content:
            no_rec = "no recommendations this turn" in agent_content.lower()
            if _has_recommendation_table(agent_content) and not no_rec:
                names = _extract_table_names(agent_content)
                if names:
                    expected_names = names  # take LAST table turn

            turns.append({"role": "assistant", "content": agent_content})

    return {
        "turns": turns,
        "expected_names": expected_names,
        "turn_count": sum(1 for t in turns if t["role"] == "user"),
    }


# ---------------------------------------------------------------------------
# Schema validator
# ---------------------------------------------------------------------------

def validate_response_schema(resp: dict) -> list:
    """Validate a single /chat API response. Returns list of violations."""
    violations = []

    reply = resp.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        violations.append("'reply' is missing or empty")

    recs = resp.get("recommendations")
    if recs is not None:
        if not isinstance(recs, list):
            violations.append("'recommendations' must be null or a list")
        else:
            if not (1 <= len(recs) <= 10):
                violations.append(
                    f"'recommendations' list length {len(recs)} is outside [1, 10]"
                )
            for i, rec in enumerate(recs):
                if not isinstance(rec.get("name"), str):
                    violations.append(f"rec[{i}]: 'name' is not a string")
                if not isinstance(rec.get("url"), str):
                    violations.append(f"rec[{i}]: 'url' is not a string")
                tt = rec.get("test_type")
                if not isinstance(tt, str):
                    violations.append(f"rec[{i}]: 'test_type' is not a string")
                else:
                    tt_normalised = re.sub(r"\s*,\s*", ",", tt.strip())
                    if not re.match(r"^[KPABSCDE](,[KPABSCDE])*$", tt_normalised):
                        violations.append(
                            f"rec[{i}]: 'test_type' value '{tt}' does not match "
                            "pattern (valid codes: K, P, A, B, S, C, D, E)"
                        )

    eoc = resp.get("end_of_conversation")
    if not isinstance(eoc, bool):
        violations.append("'end_of_conversation' is not a boolean")

    return violations


# ---------------------------------------------------------------------------
# Hallucination checker
# ---------------------------------------------------------------------------

def load_catalog_urls(catalog_path: Path) -> set:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    urls = set()
    for item in data:
        link = item.get("link", "").strip().rstrip("/")
        if link:
            urls.add(link)
    return urls


def check_hallucinations(recommendations: list, catalog_urls: set) -> list:
    hallucinated = []
    for rec in recommendations:
        url = rec.get("url", "").strip().rstrip("/")
        if url and url not in catalog_urls:
            hallucinated.append(url)
    return hallucinated


# ---------------------------------------------------------------------------
# Single-trace runner
# ---------------------------------------------------------------------------

def run_trace(
    trace_id: str,
    trace: dict,
    server_url: str,
    catalog_urls: set,
    verbose: bool = False,
    turn_delay: float = 2.0,
    retry_wait: float = 35.0,
    max_retries: int = 3,
) -> dict:
    """Replay one trace and return result dict."""
    chat_url = f"{server_url.rstrip('/')}/chat"
    trace_turns = trace["turns"]
    expected_names = trace["expected_names"]

    user_messages = [t for t in trace_turns if t["role"] == "user"]
    assistant_messages = [t for t in trace_turns if t["role"] == "assistant"]

    history = []
    final_recommendations = None
    all_schema_violations = []
    turns_used = 0
    end_of_conversation_fired = False

    for i, user_msg in enumerate(user_messages):
        if turns_used >= 8:
            break

        request_messages = history + [{"role": "user", "content": user_msg["content"]}]

        if verbose:
            print(f"\n  [{trace_id} Turn {i+1}] POST {chat_url}")
            for m in request_messages:
                snippet = m["content"][:120].replace("\n", " ")
                print(f"    [{m['role']}] {snippet}")

        try:
            resp = post_with_retry(
                chat_url,
                {"messages": request_messages},
                max_retries=max_retries,
                base_wait=int(retry_wait)
            )
            if resp is None:
                all_schema_violations.append(f"turn {i+1}: request failed or exhausted retries")
                break
        except Exception as exc:
            print(
                f"  [{trace_id} Turn {i+1}] Request failed abruptly: {exc}",
                file=sys.stderr,
            )
            all_schema_violations.append(f"turn {i+1}: abrupt request error: {exc}")
            break

        turns_used += 1

        if verbose:
            recs = resp.get("recommendations")
            recs_summary = f"{len(recs)} recs" if recs else "null"
            reply_snippet = str(resp.get("reply", ""))[:100].replace("\n", " ")
            print(
                f"    <- reply: {reply_snippet!r}"
                f" | recs: {recs_summary}"
                f" | eoc: {resp.get('end_of_conversation')}"
            )

        # Schema validation
        violations = validate_response_schema(resp)
        for v in violations:
            all_schema_violations.append(f"turn {i+1}: {v}")

        # Capture recommendations (always keep the last non-null set)
        if resp.get("recommendations") is not None:
            final_recommendations = resp["recommendations"]

        # Check end_of_conversation
        if resp.get("end_of_conversation") is True:
            end_of_conversation_fired = True

        # Inject TRACE assistant content (not API response) into history
        history.append({"role": "user", "content": user_msg["content"]})
        if i < len(assistant_messages):
            history.append(
                {"role": "assistant", "content": assistant_messages[i]["content"]}
            )
        else:
            history.append({"role": "assistant", "content": resp.get("reply", "")})

        if end_of_conversation_fired:
            break

        # Rate-limit buffer between turns
        if i < len(user_messages) - 1:
            time.sleep(turn_delay)

    # Recall@10
    retrieved_names = []
    if final_recommendations:
        retrieved_names = [r.get("name", "") for r in final_recommendations]

    retrieved_lower = [n.lower() for n in retrieved_names]
    matched_names = []
    missed_names = []
    for exp_name in expected_names:
        if exp_name.lower() in retrieved_lower:
            matched_names.append(exp_name)
        else:
            missed_names.append(exp_name)

    recall = len(matched_names) / len(expected_names) if expected_names else 0.0

    # Hallucination check on final recommendations
    hallucinated_urls = []
    if final_recommendations:
        hallucinated_urls = check_hallucinations(final_recommendations, catalog_urls)

    return {
        "recall_at_10": recall,
        "expected_names": expected_names,
        "retrieved_names": retrieved_names,
        "matched_names": matched_names,
        "missed_names": missed_names,
        "hallucinated_urls": hallucinated_urls,
        "schema_violations": all_schema_violations,
        "turns_used": turns_used,
        "end_of_conversation_fired": end_of_conversation_fired,
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def health_check(server_url: str, timeout: int = 10) -> None:
    health_url = f"{server_url.rstrip('/')}/health"
    print(f"Checking server health at {health_url} ...")
    try:
        resp = requests.get(health_url, timeout=timeout).json()
        status_val = resp.get("status", "unknown")
        print(f"  Server status: {status_val}")
        if status_val != "healthy":
            print(
                f"ERROR: Server responded but status is '{status_val}'. Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as exc:
        print(
            f"\nERROR: Cannot reach server at {server_url}.\n"
            f"  Cause: {exc}\n"
            f"  Make sure the server is running:\n"
            f"    uvicorn app.main:app --host 0.0.0.0 --port 8000\n",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Table printer
# ---------------------------------------------------------------------------

def _schema_ok(violations: list) -> str:
    return "OK" if not violations else f"FAIL({len(violations)})"


def print_table(results: dict) -> None:
    header = (
        f"{'Trace':<6} {'Turns':>5} {'Expected':>8} "
        f"{'Retrieved':>9} {'Recall@10':>9} {'Hallucinations':>14} {'Schema OK':>10}"
    )
    divider = "-" * len(header)
    print()
    print(divider)
    print(header)
    print(divider)

    recall_vals = []
    turns_vals = []
    expected_vals = []
    retrieved_vals = []
    halluc_vals = []
    schema_all_ok = True

    for trace_id in sorted(results.keys(), key=lambda x: int(x[1:])):
        r = results[trace_id]
        recall = r["recall_at_10"]
        recall_vals.append(recall)
        turns_vals.append(r["turns_used"])
        expected_vals.append(len(r["expected_names"]))
        retrieved_vals.append(len(r["retrieved_names"]))
        halluc_vals.append(len(r["hallucinated_urls"]))
        if r["schema_violations"]:
            schema_all_ok = False

        print(
            f"{trace_id:<6} "
            f"{r['turns_used']:>5} "
            f"{len(r['expected_names']):>8} "
            f"{len(r['retrieved_names']):>9} "
            f"{recall:>9.3f} "
            f"{len(r['hallucinated_urls']):>14} "
            f"{_schema_ok(r['schema_violations']):>10}"
        )

    print(divider)
    n = len(recall_vals)
    mean_recall = sum(recall_vals) / n if n else 0.0
    mean_turns = sum(turns_vals) / n if n else 0.0
    mean_expected = sum(expected_vals) / n if n else 0.0
    mean_retrieved = sum(retrieved_vals) / n if n else 0.0
    total_halluc = sum(halluc_vals)

    print(
        f"{'MEAN':<6} "
        f"{mean_turns:>5.1f} "
        f"{mean_expected:>8.1f} "
        f"{mean_retrieved:>9.1f} "
        f"{mean_recall:>9.3f} "
        f"{total_halluc:>14} "
        f"{'OK' if schema_all_ok else 'FAIL':>10}"
    )
    print(divider)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Replay evaluation harness for SHL Assessment Recommendation Agent"
    )
    parser.add_argument(
        "--traces",
        default="data/traces/",
        help="Directory containing C1.md-C10.md  [default: data/traces/]",
    )
    parser.add_argument(
        "--trace",
        type=str,
        default=None,
        help="Run only this trace (e.g. C1). Omit to run all traces.",
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Base URL for the API  [default: http://localhost:8000]",
    )
    parser.add_argument(
        "--output",
        default="eval/results/recall_report.json",
        help="Path for JSON report  [default: eval/results/recall_report.json]",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each turn's request and response",
    )
    parser.add_argument(
        "--turn-delay",
        type=float,
        default=2.0,
        help="Seconds to wait between turns  [default: 2.0]",
    )
    parser.add_argument(
        "--trace-delay",
        type=float,
        default=10.0,
        help="Seconds to wait between traces  [default: 10.0]",
    )
    parser.add_argument(
        "--retry-wait",
        type=float,
        default=35.0,
        help="Base wait seconds on 429 before retry  [default: 35]",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per turn on 429  [default: 3]",
    )
    args = parser.parse_args(argv)

    traces_dir = Path(args.traces)
    if not traces_dir.is_dir():
        print(f"ERROR: Traces directory not found: {traces_dir}", file=sys.stderr)
        sys.exit(1)

    # Locate catalog.json
    catalog_candidates = [
        Path("catalog/catalog.json"),
        traces_dir.parent.parent / "catalog" / "catalog.json",
        Path(__file__).parent.parent / "catalog" / "catalog.json",
    ]
    catalog_path = None
    for c in catalog_candidates:
        if c.is_file():
            catalog_path = c
            break
    if catalog_path is None:
        print(
            "ERROR: Could not locate catalog/catalog.json. "
            "Run from the project root.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading catalog from {catalog_path} ...")
    catalog_urls = load_catalog_urls(catalog_path)
    print(f"  Catalog: {len(catalog_urls)} unique URLs loaded.")

    # Health check — hard exit if not reachable
    health_check(args.server, timeout=10)

    # Discover trace files C1–C10
    trace_files = {}
    for i in range(1, 11):
        f = traces_dir / f"C{i}.md"
        if f.is_file():
            trace_files[f"C{i}"] = f
        else:
            print(f"WARNING: Trace file not found: {f}", file=sys.stderr)

    if not trace_files:
        print("ERROR: No trace files found. Aborting.", file=sys.stderr)
        sys.exit(1)

    if args.trace:
        trace_files = {
            k: v for k, v in trace_files.items() 
            if k == args.trace
        }
        if not trace_files:
            print(f"ERROR: trace '{args.trace}' not found")
            sys.exit(1)

    print(f"\nRunning evaluation on {len(trace_files)} traces ...\n")

    results = {}

    for trace_id in sorted(trace_files.keys(), key=lambda x: int(x[1:])):
        trace_path = trace_files[trace_id]
        print(f"  Parsing {trace_id} ({trace_path.name}) ...", end=" ", flush=True)

        try:
            trace = parse_trace(trace_path)
        except Exception as exc:
            print(f"PARSE ERROR: {exc}", file=sys.stderr)
            results[trace_id] = {
                "recall_at_10": 0.0,
                "expected_names": [],
                "retrieved_names": [],
                "matched_names": [],
                "missed_names": [],
                "hallucinated_urls": [],
                "schema_violations": [f"parse error: {exc}"],
                "turns_used": 0,
                "end_of_conversation_fired": False,
            }
            continue

        print(
            f"{trace['turn_count']} user turns, "
            f"{len(trace['expected_names'])} expected",
            flush=True,
        )

        if args.verbose:
            print(f"  Expected names: {trace['expected_names']}")

        try:
            result = run_trace(
                trace_id=trace_id,
                trace=trace,
                server_url=args.server,
                catalog_urls=catalog_urls,
                verbose=args.verbose,
                turn_delay=args.turn_delay,
                retry_wait=args.retry_wait,
                max_retries=args.max_retries,
            )
        except Exception as exc:
            print(
                f"  [{trace_id}] Unexpected runner error: {exc}",
                file=sys.stderr,
            )
            result = {
                "recall_at_10": 0.0,
                "expected_names": trace["expected_names"],
                "retrieved_names": [],
                "matched_names": [],
                "missed_names": list(trace["expected_names"]),
                "hallucinated_urls": [],
                "schema_violations": [f"runner error: {exc}"],
                "turns_used": 0,
                "end_of_conversation_fired": False,
            }

        results[trace_id] = result

        recall = result["recall_at_10"]
        halluc = len(result["hallucinated_urls"])
        schema_status = "OK" if not result["schema_violations"] else f"FAIL({len(result['schema_violations'])})"
        print(
            f"    {trace_id}: Recall@10={recall:.3f}  "
            f"turns={result['turns_used']}  "
            f"hallucinations={halluc}  "
            f"schema={schema_status}"
        )
        if result["missed_names"]:
            print(f"    Missed: {result['missed_names']}")

        # Pause between traces to respect LLM provider rate limits
        remaining = [
            k for k in sorted(trace_files.keys(), key=lambda x: int(x[1:]))
            if k > trace_id
        ]
        if remaining:
            print(f"  Waiting {args.trace_delay:.0f}s before next trace ...")
            time.sleep(args.trace_delay)

    # Print formatted table
    print_table(results)

    # Compute mean recall
    recall_vals = [r["recall_at_10"] for r in results.values()]
    mean_recall = sum(recall_vals) / len(recall_vals) if recall_vals else 0.0

    # Write JSON report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "mean_recall_at_10": round(mean_recall, 4),
        "traces": results,
    }
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"JSON report written to: {output_path}")
    print(f"Mean Recall@10: {mean_recall:.4f}")


if __name__ == "__main__":
    main()
