"""Catalog loading utilities for JSON-based assessment datasets."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from config import get_logger

from catalog.models import Assessment

logger = get_logger(__name__)


class CatalogLoadError(Exception):
    """Raised when catalog loading fails."""


class CatalogFormatError(Exception):
    """Raised when catalog JSON structure is invalid."""


def load_raw_catalog(path: Path | str) -> list[dict[str, object]]:
    """Load raw catalog records from JSON file.

    Args:
        path: Path to source JSON file.

    Returns:
        Raw record dictionaries.

    Raises:
        CatalogLoadError: For missing files, decoding errors, or read errors.
        CatalogFormatError: For invalid top-level JSON schema.
    """
    source_path = Path(path)
    if not source_path.exists():
        raise CatalogLoadError(f"Catalog file not found: {source_path}")

    try:
        content = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogLoadError(f"Unable to read catalog file: {source_path}") from exc

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise CatalogLoadError(f"Malformed JSON in catalog file: {source_path}") from exc

    if not isinstance(payload, list):
        raise CatalogFormatError("Catalog top-level structure must be a JSON array")

    records: list[dict[str, object]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise CatalogFormatError(f"Catalog record at index {index} must be an object")
        records.append(item)

    logger.info("Loaded raw catalog records: count=%s source=%s", len(records), source_path)
    return records


def load_assessments(path: Path | str) -> list[Assessment]:
    """Load canonical catalog records as Assessment models.

    Args:
        path: Path to canonical catalog JSON file.

    Returns:
        Parsed Assessment objects.

    Raises:
        CatalogLoadError: If model parsing fails.
    """
    records = load_raw_catalog(path)
    assessments: list[Assessment] = []

    for index, record in enumerate(records):
        try:
            assessments.append(Assessment.model_validate(record))
        except ValidationError as exc:
            raise CatalogLoadError(f"Invalid canonical record at index {index}") from exc

    logger.info("Loaded canonical assessments: count=%s source=%s", len(assessments), path)
    return assessments
