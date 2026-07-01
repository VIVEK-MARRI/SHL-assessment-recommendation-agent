"""Unit tests for end-to-end catalog build pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from catalog import build_canonical_catalog
from catalog.validator import CatalogValidationError


VALID_RECORD = {
    "entity_id": " SHL-500 ",
    "name": "  Example\nAssessment ",
    "link": " WWW.SHL.COM/example-assessment/ ",
    "description": "  Valid\u200b description ",
    "keys": "knowledge and skills; competencies",
    "job_levels": "junior, senior",
    "job_levels_raw": " junior, senior ",
    "languages": "en; english",
    "languages_raw": " en ",
    "duration": " 35 minutes ",
    "duration_raw": " 35 minutes ",
    "status": "published",
    "remote": "true",
    "adaptive": "false",
}


def test_build_canonical_catalog_success(tmp_path: Path) -> None:
    """Pipeline should clean, normalize, validate, and export catalog."""
    source = tmp_path / "raw_catalog.json"
    destination = tmp_path / "catalog.json"
    source.write_text(json.dumps([VALID_RECORD]), encoding="utf-8")

    assessments = build_canonical_catalog(source, destination)

    assert len(assessments) == 1
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload[0]["entity_id"] == "SHL-500"
    assert payload[0]["name"] == "Example Assessment"
    assert payload[0]["keys"] == ["Knowledge & Skills", "Competencies"]
    assert payload[0]["status"] == "active"


def test_build_canonical_catalog_rejects_duplicates(tmp_path: Path) -> None:
    """Pipeline should reject duplicate records with validation error."""
    source = tmp_path / "raw_catalog.json"
    duplicate = dict(VALID_RECORD)
    duplicate["entity_id"] = "SHL-500"
    duplicate["name"] = "Another Name"
    duplicate["link"] = "https://www.shl.com/example-assessment"

    source.write_text(json.dumps([VALID_RECORD, duplicate]), encoding="utf-8")

    with pytest.raises(CatalogValidationError):
        build_canonical_catalog(source, tmp_path / "catalog.json")
