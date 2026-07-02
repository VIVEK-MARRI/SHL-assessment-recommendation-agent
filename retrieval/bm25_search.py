"""Low-level BM25 search for lexical assessment retrieval."""

from __future__ import annotations

import logging
import math
import re
from time import perf_counter

import numpy as np
from rank_bm25 import BM25Okapi

from retrieval.bm25_models import BM25DocumentRecord
from retrieval.retrieval_models import RetrievedAssessment

logger = logging.getLogger(__name__)

_SECTION_RE_TEMPLATE = r"{label}:\n(?P<value>.*?)(?=\n\n[A-Za-z ]+:\n|\Z)"
_DURATION_RE = re.compile(r"(\d+)")
_CATEGORY_CODE_RE = re.compile(r"\(([^)]+)\)")


class BM25SearchError(Exception):
    """Raised when BM25 lexical search cannot be completed."""


def search_bm25(
    index: BM25Okapi,
    documents: list[BM25DocumentRecord],
    query_tokens: list[str],
    top_k: int = 20,
    minimum_score: float = 0.0,
) -> list[RetrievedAssessment]:
    """Search a loaded BM25 index and resolve document metadata.

    Args:
        index: Loaded ``BM25Okapi`` instance.
        documents: BM25 document records ordered by corpus offset.
        query_tokens: Tokenized user query.
        top_k: Maximum number of candidates to return.
        minimum_score: Minimum raw BM25 score to include.

    Returns:
        Ranked lexical retrieval candidates sorted by descending score.

    Raises:
        BM25SearchError: If parameters, corpus alignment, or scoring fail.
    """
    started_at = perf_counter()
    if top_k < 1:
        raise BM25SearchError("top_k must be greater than or equal to 1")
    if not math.isfinite(minimum_score):
        raise BM25SearchError("minimum_score must be finite")
    if not query_tokens:
        raise BM25SearchError("query_tokens must not be empty")
    if len(index.doc_len) != len(documents):
        raise BM25SearchError(
            f"Corpus mismatch: BM25 index has {len(index.doc_len)} documents but "
            f"corpus has {len(documents)} records."
        )

    try:
        scores = np.asarray(index.get_scores(query_tokens), dtype=np.float64)
    except Exception as exc:
        raise BM25SearchError(f"BM25 scoring failed: {exc}") from exc
    if scores.ndim != 1 or scores.shape[0] != len(documents):
        raise BM25SearchError("BM25 scoring returned an invalid score vector")

    ranked_offsets = sorted(
        range(len(documents)),
        key=lambda offset: (-float(scores[offset]), offset),
    )
    logger.info(
        "BM25 search complete: top_k=%d elapsed_ms=%.2f",
        top_k,
        (perf_counter() - started_at) * 1000,
    )

    results: list[RetrievedAssessment] = []
    seen_entity_ids: set[str] = set()
    for bm25_rank, offset in enumerate(ranked_offsets, start=1):
        score = float(scores[offset])
        if score < minimum_score:
            continue
        record = documents[offset]
        if record.entity_id in seen_entity_ids:
            continue
        seen_entity_ids.add(record.entity_id)
        results.append(
            _to_retrieved_assessment(
                record=record,
                score=score,
                rank=len(results) + 1,
                bm25_rank=bm25_rank,
            )
        )
        if len(results) >= top_k:
            break

    logger.info(
        "Metadata resolved and results returned: count=%d elapsed_ms=%.2f",
        len(results),
        (perf_counter() - started_at) * 1000,
    )
    return results


def _to_retrieved_assessment(
    record: BM25DocumentRecord,
    score: float,
    rank: int,
    bm25_rank: int,
) -> RetrievedAssessment:
    """Convert a BM25 corpus record into the shared retrieval result model."""
    parsed = _parse_legacy_document(record.document)
    return RetrievedAssessment(
        retrieval_source="bm25",
        entity_id=record.entity_id,
        name=record.name or parsed["name"] or record.entity_id,
        description=record.description,
        url=record.url or f"https://www.shl.com/products/product-catalog/view/{record.entity_id}",
        test_type=record.test_type or parsed["test_type"],
        score=score,
        rank=rank,
        embedding_rank=None,
        bm25_rank=bm25_rank,
        job_levels=record.job_levels or parsed["job_levels"],
        languages=record.languages or parsed["languages"],
        duration=record.duration or parsed["duration"],
        duration_minutes=(
            record.duration_minutes
            if record.duration_minutes is not None
            else _parse_duration_minutes(parsed["duration"])
        ),
        remote=record.remote if record.remote is not None else parsed["remote"],
        adaptive=record.adaptive if record.adaptive is not None else parsed["adaptive"],
        keys=record.keys or parsed["keys"],
    )


def _parse_legacy_document(document: str) -> dict:
    """Parse metadata from pre-Module-10 BM25 corpus document text."""
    categories = _section(document, "Categories")
    return {
        "name": _section(document, "Name"),
        "keys": _parse_category_names(categories),
        "test_type": _parse_category_codes(categories),
        "job_levels": _split_list(_section(document, "Job Levels")),
        "languages": _split_list(_section(document, "Languages")),
        "duration": _section(document, "Duration"),
        "remote": _yes_no(_section(document, "Remote"), default=True),
        "adaptive": _yes_no(_section(document, "Adaptive"), default=False),
    }


def _section(document: str, label: str) -> str:
    pattern = re.compile(_SECTION_RE_TEMPLATE.format(label=re.escape(label)), re.DOTALL)
    match = pattern.search(document)
    return match.group("value").strip() if match else ""


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_category_names(value: str) -> list[str]:
    names: list[str] = []
    for item in _split_list(value):
        names.append(_CATEGORY_CODE_RE.sub("", item).strip())
    return [name for name in names if name]


def _parse_category_codes(value: str) -> str:
    codes = _CATEGORY_CODE_RE.findall(value)
    return "|".join(dict.fromkeys(code.strip() for code in codes if code.strip()))


def _parse_duration_minutes(duration: str) -> int | None:
    if not duration or duration.lower() in ("untimed", "variable", "unknown"):
        return None
    match = _DURATION_RE.search(duration)
    return int(match.group(1)) if match else None


def _yes_no(value: str, *, default: bool) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"yes", "true", "1"}
