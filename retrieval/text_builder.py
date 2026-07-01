"""Builds deterministic plain-text search documents from Assessment objects.

Each document is a structured, label-headed string that captures all
semantic content of an assessment without including URLs or entity IDs,
which are identifiers rather than semantic content.

Design notes
------------
* ``Test Type`` codes (K, P, A, …) are included so the embedding model
  can capture explicit category signal.  A user asking for a "cognitive
  ability test" maps neatly to type-A documents even when the description
  does not use that exact phrasing.
* Duration is expressed as both a human phrase ("30 minutes") and as
  a numeric hint ("~30 min") so the model encodes approximate length.
"""

from __future__ import annotations

import logging

from catalog.models import Assessment
from retrieval.constants import DOCUMENT_TEMPLATE

logger = logging.getLogger(__name__)


def _derive_test_type_label(keys: list[str]) -> str:
    """Return a human-readable label for the test type codes.

    Args:
        keys: Category keys from the assessment.

    Returns:
        Comma-joined full category names, or ``"None"`` if empty.
    """
    return ", ".join(keys) if keys else "None"


def build_document(assessment: Assessment) -> str:
    """Build a single, deterministic semantic search document for an assessment.

    The returned string uses a consistent labelled-section format so that
    the embedding model can capture the full semantic meaning of each
    assessment.  URLs and entity IDs are intentionally excluded because
    they are identifiers, not content.

    Args:
        assessment: Canonical assessment record from the catalog.

    Returns:
        Deterministic, non-empty UTF-8 string suitable for embedding.
    """
    # Test type: both short codes and full names maximise recall
    from catalog.constants import KEY_TO_TEST_TYPE_MAP
    type_codes = "|".join(
        dict.fromkeys(
            KEY_TO_TEST_TYPE_MAP[k] for k in assessment.keys if k in KEY_TO_TEST_TYPE_MAP
        )
    )
    categories = _derive_test_type_label(assessment.keys)
    type_section = f"{categories} ({type_codes})" if type_codes else categories

    job_levels = ", ".join(assessment.job_levels) if assessment.job_levels else "None"
    languages = ", ".join(assessment.languages) if assessment.languages else "None"
    duration = assessment.duration if assessment.duration else "Unknown"
    remote = "Yes" if assessment.remote else "No"
    adaptive = "Yes" if assessment.adaptive else "No"

    document = DOCUMENT_TEMPLATE.format(
        name=assessment.name,
        description=assessment.description,
        categories=type_section,
        job_levels=job_levels,
        languages=languages,
        duration=duration,
        status=assessment.status,
        remote=remote,
        adaptive=adaptive,
    )
    logger.debug("Built document for assessment entity_id=%s", assessment.entity_id)
    return document
