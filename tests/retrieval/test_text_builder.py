"""Unit tests for retrieval.text_builder.build_document."""

from __future__ import annotations

import pytest

from catalog.models import Assessment
from retrieval.text_builder import build_document

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_assessment(**overrides) -> Assessment:
    """Return a minimal valid Assessment, optionally overriding fields."""
    defaults = dict(
        entity_id="1",
        name="Test Assessment",
        link="https://www.shl.com/products/product-catalog/view/test/",
        description="A test description.",
        keys=["Knowledge & Skills"],
        job_levels=["Graduate"],
        job_levels_raw="Graduate,",
        languages=["English (US)"],
        languages_raw="English (USA),",
        duration="30 minutes",
        duration_raw="Approximate Completion Time in minutes = 30",
        status="active",
        remote=True,
        adaptive=False,
    )
    defaults.update(overrides)
    return Assessment.model_validate(defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBuildDocument:
    def test_contains_name(self):
        doc = build_document(_make_assessment(name="Alpha Test"))
        assert "Alpha Test" in doc

    def test_contains_description(self):
        doc = build_document(_make_assessment(description="Unique description here."))
        assert "Unique description here." in doc

    def test_contains_categories(self):
        doc = build_document(_make_assessment(keys=["Simulations", "Competencies"]))
        assert "Simulations" in doc
        assert "Competencies" in doc

    def test_contains_job_levels(self):
        doc = build_document(_make_assessment(job_levels=["Director", "Executive"]))
        assert "Director" in doc
        assert "Executive" in doc

    def test_contains_languages(self):
        doc = build_document(_make_assessment(languages=["English (US)"]))
        assert "English (US)" in doc

    def test_contains_duration(self):
        doc = build_document(_make_assessment(duration="45 minutes"))
        assert "45 minutes" in doc

    def test_contains_status(self):
        doc = build_document(_make_assessment(status="active"))
        assert "active" in doc

    def test_remote_yes(self):
        doc = build_document(_make_assessment(remote=True))
        assert "Yes" in doc

    def test_adaptive_no(self):
        doc = build_document(_make_assessment(adaptive=False))
        # "No" appears for adaptive
        assert "No" in doc

    def test_no_url_in_document(self):
        doc = build_document(_make_assessment(link="https://www.shl.com/some/path/"))
        assert "https://" not in doc

    def test_no_entity_id_in_document(self):
        assessment = _make_assessment(entity_id="99999")
        doc = build_document(assessment)
        assert "99999" not in doc

    def test_deterministic(self):
        assessment = _make_assessment()
        assert build_document(assessment) == build_document(assessment)

    def test_empty_keys_shows_none(self):
        # Empty keys list is tricky because validator accepts it
        a = Assessment.model_validate(
            dict(
                entity_id="2",
                name="No Category",
                link="https://www.shl.com/x/",
                description="desc",
                keys=[],
                job_levels=[],
                job_levels_raw="",
                languages=[],
                languages_raw="",
                duration="",
                duration_raw="",
                status="active",
                remote=False,
                adaptive=False,
            )
        )
        doc = build_document(a)
        assert "None" in doc

    def test_section_headers_present(self):
        doc = build_document(_make_assessment())
        for header in ("Name:", "Description:", "Categories:", "Job Levels:", "Languages:",
                        "Duration:", "Status:", "Remote:", "Adaptive:"):
            assert header in doc, f"Missing section header: {header}"

    def test_returns_non_empty_string(self):
        doc = build_document(_make_assessment())
        assert isinstance(doc, str)
        assert len(doc) > 50
