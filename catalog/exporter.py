"""Catalog exporter for deterministic canonical JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from config import get_logger

from catalog.constants import ASSESSMENT_FIELD_ORDER
from catalog.models import Assessment

logger = get_logger(__name__)


class CatalogExportError(Exception):
    """Raised when catalog export fails."""


def _ordered_record(assessment: Assessment) -> dict[str, object]:
    """Create stable ordered dict for JSON output.

    Args:
        assessment: Assessment object.

    Returns:
        Deterministically ordered dictionary.
    """
    data = assessment.model_dump()
    return {field: data[field] for field in ASSESSMENT_FIELD_ORDER}


def export_catalog(assessments: list[Assessment], path: Path | str) -> None:
    """Export canonical assessments to UTF-8 pretty JSON.

    Args:
        assessments: Canonical assessment records.
        path: Destination JSON path.

    Returns:
        None

    Raises:
        CatalogExportError: If write operation fails.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    sorted_assessments = sorted(
        assessments,
        key=lambda item: (item.name.casefold(), item.entity_id.casefold()),
    )
    payload = [_ordered_record(assessment) for assessment in sorted_assessments]

    try:
        with destination.open("w", encoding="utf-8", newline="\n") as output_file:
            json.dump(payload, output_file, indent=2, ensure_ascii=False)
            output_file.write("\n")
    except OSError as exc:
        raise CatalogExportError(f"Failed to export catalog to {destination}") from exc

    logger.info("Canonical catalog exported: count=%s destination=%s", len(payload), destination)
