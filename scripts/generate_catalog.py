"""CLI entry point for generating the canonical SHL catalog.

This script is a thin wrapper only. All pipeline logic lives in
the catalog package (catalog/__init__.py).

Usage::

    py scripts/generate_catalog.py
    py scripts/generate_catalog.py --output path/to/custom_catalog.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root (parent of scripts/) is on sys.path so that
# `catalog` and `config` are importable when running this script directly.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from catalog import build_canonical_catalog  # noqa: E402
from config import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Parse CLI arguments and run the catalog generation pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate the canonical SHL catalog from raw_catalog.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional output path for the generated catalog.json file.",
    )
    args = parser.parse_args()

    try:
        from typing import Any
        kwargs: dict[str, Any] = {}
        if args.output is not None:
            kwargs["output_path"] = args.output

        assessments = build_canonical_catalog(**kwargs)
        logger.info(
            "Catalog generation complete: %d assessments exported.",
            len(assessments),
        )
        sys.exit(0)
    except Exception as exc:
        print(f"Catalog generation failed: {exc}")
        logger.error("Catalog generation failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
