"""CLI entry point for building the BM25 lexical index.

This script is a thin wrapper only.  All pipeline logic lives in
retrieval.bm25_builder.build_bm25_index_pipeline().

Usage::

    py scripts/build_bm25_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (parent of scripts/) is on sys.path.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import get_logger  # noqa: E402
from retrieval import build_bm25_index  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Run the BM25 index build pipeline and exit with appropriate code."""
    try:
        build_bm25_index()
        logger.info("build_bm25_index completed successfully.")
        sys.exit(0)
    except Exception as exc:
        logger.error("build_bm25_index failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
