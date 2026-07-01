"""Generates Markdown and JSON reports from evaluation results."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "reports"


def _ensure_reports_dir() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def generate_json_report(results: dict, name: str = "eval") -> Path:
    """Write results dict to a timestamped JSON file. Returns the path."""
    _ensure_reports_dir()
    path = REPORTS_DIR / f"{name}_{_ts()}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("JSON report saved: %s", path)
    return path


def generate_markdown_report(results: dict, name: str = "eval") -> Path:
    """Write a Markdown report from results. Returns the path."""
    _ensure_reports_dir()
    path = REPORTS_DIR / f"{name}_{_ts()}.md"

    lines = [
        f"# SHL Assessment Agent — Evaluation Report",
        f"",
        f"**Generated:** {datetime.utcnow().isoformat()}Z  ",
        f"**Run:** `{name}`",
        f"",
    ]

    for section, data in results.items():
        lines.append(f"## {section.replace('_', ' ').title()}")
        lines.append("")
        if isinstance(data, dict):
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in data.items():
                if isinstance(v, dict):
                    # Nested dict — render as sub-table
                    lines.append(f"| **{k}** | |")
                    for kk, vv in v.items():
                        lines.append(f"| &nbsp;&nbsp;`{kk}` | `{vv}` |")
                else:
                    lines.append(f"| `{k}` | `{v}` |")
            lines.append("")
        else:
            lines.append(str(data))
            lines.append("")

    content = "\n".join(lines)
    with path.open("w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Markdown report saved: %s", path)
    return path


def print_summary(results: dict) -> None:
    """Print a human-readable console summary."""
    print("\n" + "=" * 70)
    print("  SHL ASSESSMENT AGENT - EVALUATION SUMMARY")
    print("=" * 70)
    for section, data in results.items():
        print(f"\n{'-' * 70}")
        print(f"  {section.upper()}")
        print(f"{'-' * 70}")
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for kk, vv in v.items():
                        print(f"    {kk:<20} {vv}")
                else:
                    print(f"  {k:<30} {v}")
    print("\n" + "=" * 70 + "\n")
