"""Unit tests for catalog validation and duplicate detection."""

from __future__ import annotations

import pytest

from catalog.validator import CatalogValidationError, detect_duplicates, raise_if_invalid, validate_records


def _valid_record(entity_id: str, name: str, link: str) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "name": name,
        "link": link,
        "description": "Valid description",
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


def test_validate_records_success() -> None:
    """Validator should produce a clean report for valid records."""
    report = validate_records([_valid_record("SHL-1", "A", "https://www.shl.com/a")])
    assert report.total_records == 1
    assert report.invalid_records == 0
    assert report.duplicate_records == 0


def test_validate_records_missing_required_field() -> None:
    """Missing required field should create validation issues."""
    record = _valid_record("SHL-1", "A", "https://www.shl.com/a")
    record["name"] = ""

    report = validate_records([record])
    assert report.invalid_records == 1
    assert len(report.issues) >= 1


def test_validate_records_invalid_url() -> None:
    """Invalid URL should be reported as validation issue."""
    record = _valid_record("SHL-1", "A", "not-a-url")
    report = validate_records([record])
    assert any(issue.field == "link" for issue in report.issues)


def test_detect_duplicates_by_id_name_and_url() -> None:
    """Duplicate ids, names, and urls should be detected."""
    records = [
        _valid_record("SHL-1", "Assessment A", "https://www.shl.com/a"),
        _valid_record("SHL-1", "Assessment A", "https://www.shl.com/a/"),
    ]

    issues = detect_duplicates(records)
    fields = {issue.field for issue in issues}
    assert "entity_id" in fields
    assert "name" in fields
    assert "link" in fields


def test_raise_if_invalid_raises_on_issues() -> None:
    """raise_if_invalid should raise when report has issues."""
    report = validate_records([_valid_record("", "A", "https://www.shl.com/a")])
    with pytest.raises(CatalogValidationError):
        raise_if_invalid(report)
