"""Unit tests for catalog normalization behavior."""

from __future__ import annotations

from catalog.normalizer import (
    normalize_category,
    normalize_job_level,
    normalize_language,
    normalize_record,
    normalize_status,
)


def test_normalize_category_aliases() -> None:
    """Category aliases should map to canonical names."""
    assert normalize_category("knowledge and skills") == "Knowledge & Skills"


def test_normalize_language_aliases() -> None:
    """Language aliases should map to canonical language values."""
    assert normalize_language("en") == "English"


def test_normalize_job_level_aliases() -> None:
    """Job level aliases should map to canonical values."""
    assert normalize_job_level("junior") == "Entry Level"


def test_normalize_status_aliases() -> None:
    """Status aliases should map to canonical status values."""
    assert normalize_status("Live") == "active"


def test_normalize_record_fields() -> None:
    """Record normalization should normalize key list-like fields."""
    record = {
        "keys": ["knowledge and skills"],
        "languages": ["en"],
        "job_levels": ["junior"],
        "status": "published",
        "link": "HTTPS://WWW.SHL.COM/Assessment/#fragment",
    }

    normalized = normalize_record(record)

    assert normalized["keys"] == ["Knowledge & Skills"]
    assert normalized["languages"] == ["English"]
    assert normalized["job_levels"] == ["Entry Level"]
    assert normalized["status"] == "active"
    assert normalized["link"] == "https://www.shl.com/Assessment"
