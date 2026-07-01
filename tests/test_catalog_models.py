"""Unit tests for catalog Assessment model validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from catalog.models import Assessment


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


def test_assessment_model_valid() -> None:
    """Assessment model should parse a valid record."""
    assessment = Assessment.model_validate(VALID_RECORD)
    assert assessment.entity_id == "SHL-100"
    assert assessment.remote is True


def test_assessment_model_missing_field_raises() -> None:
    """Missing required fields should raise validation errors."""
    payload = dict(VALID_RECORD)
    payload.pop("name")

    with pytest.raises(ValidationError):
        Assessment.model_validate(payload)


def test_assessment_model_invalid_url_raises() -> None:
    """Malformed URL should fail model validation."""
    payload = dict(VALID_RECORD)
    payload["link"] = "not-a-url"

    with pytest.raises(ValidationError):
        Assessment.model_validate(payload)
