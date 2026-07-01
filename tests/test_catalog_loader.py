"""Unit tests for catalog loader behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from catalog.loader import CatalogFormatError, CatalogLoadError, load_assessments, load_raw_catalog


VALID_RECORD = {
    "entity_id": "SHL-100",
    "name": "Assessment A",
    "link": "https://www.shl.com/assessment-a",
    "description": "Valid description.",
    "keys": ["Knowledge & Skills"],
    "job_levels": ["Entry Level"],
    "job_levels_raw": "Entry Level",
    "languages": ["English"],
    "languages_raw": "English",
    "duration": "30 minutes",
    "duration_raw": "30 minutes",
    "status": "active",
    "remote": True,
    "adaptive": False,
}


def test_load_raw_catalog_success(tmp_path: Path) -> None:
    """Loader should return list of record dictionaries from valid JSON."""
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps([VALID_RECORD]), encoding="utf-8")

    records = load_raw_catalog(catalog_path)
    assert len(records) == 1


def test_load_raw_catalog_missing_file_raises() -> None:
    """Missing file should raise CatalogLoadError."""
    with pytest.raises(CatalogLoadError):
        load_raw_catalog("does-not-exist.json")


def test_load_raw_catalog_malformed_json_raises(tmp_path: Path) -> None:
    """Malformed JSON should raise CatalogLoadError."""
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{bad-json", encoding="utf-8")

    with pytest.raises(CatalogLoadError):
        load_raw_catalog(catalog_path)


def test_load_raw_catalog_invalid_top_level_raises(tmp_path: Path) -> None:
    """Non-list top-level JSON should raise CatalogFormatError."""
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({"a": 1}), encoding="utf-8")

    with pytest.raises(CatalogFormatError):
        load_raw_catalog(catalog_path)


def test_load_assessments_invalid_record_raises(tmp_path: Path) -> None:
    """Invalid canonical record should raise CatalogLoadError."""
    invalid = dict(VALID_RECORD)
    invalid["link"] = "invalid-url"
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps([invalid]), encoding="utf-8")

    with pytest.raises(CatalogLoadError):
        load_assessments(catalog_path)
