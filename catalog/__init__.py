"""Catalog management package for canonical SHL assessment data infrastructure."""

from __future__ import annotations

import time
from pathlib import Path

from config import get_logger

from catalog.cleaner import clean_record
from catalog.constants import CANONICAL_CATALOG_DEFAULT_PATH, RAW_CATALOG_DEFAULT_PATH
from catalog.exporter import export_catalog
from catalog.loader import load_assessments, load_raw_catalog
from catalog.models import Assessment
from catalog.normalizer import normalize_record
from catalog.validator import raise_if_invalid, validate_records

logger = get_logger(__name__)


def build_canonical_catalog(
    input_path: Path | str = RAW_CATALOG_DEFAULT_PATH,
    output_path: Path | str = CANONICAL_CATALOG_DEFAULT_PATH,
) -> list[Assessment]:
    """Build canonical validated catalog from source JSON input.

    Args:
        input_path: Source catalog path.
        output_path: Destination canonical catalog path.

    Returns:
        Canonical assessment records.

    Raises:
        catalog.validator.CatalogValidationError: If validation fails.
        catalog.loader.CatalogLoadError: If source loading fails.
        catalog.exporter.CatalogExportError: If export fails.
    """
    started = time.perf_counter()
    logger.info("Catalog build started: input=%s output=%s", input_path, output_path)

    raw_records = load_raw_catalog(input_path)
    cleaned_records = [clean_record(record) for record in raw_records]
    normalized_records = [normalize_record(record) for record in cleaned_records]

    validation_report = validate_records(normalized_records)
    raise_if_invalid(validation_report)

    assessments = [Assessment.model_validate(record) for record in normalized_records]
    export_catalog(assessments, output_path)

    elapsed = round(time.perf_counter() - started, 6)
    logger.info("Catalog build completed: records=%s elapsed=%ss", len(assessments), elapsed)
    return assessments


def load_canonical_catalog(path: Path | str = CANONICAL_CATALOG_DEFAULT_PATH) -> list[Assessment]:
    """Load canonical catalog for downstream consumption.

    Args:
        path: Canonical catalog path.

    Returns:
        Canonical assessment records.
    """
    return load_assessments(path)


__all__ = [
    "Assessment",
    "build_canonical_catalog",
    "load_canonical_catalog",
]
