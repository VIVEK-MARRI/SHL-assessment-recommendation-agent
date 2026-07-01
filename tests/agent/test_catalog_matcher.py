"""Unit tests for CatalogMatcher (Module 15)."""

from __future__ import annotations

import pytest

from agent.catalog_matcher import CatalogMatcher, CatalogLoadError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def matcher() -> CatalogMatcher:
    m = CatalogMatcher()
    m.load()
    return m


# ---------------------------------------------------------------------------
# Catalog loading
# ---------------------------------------------------------------------------

def test_catalog_loads(matcher: CatalogMatcher) -> None:
    assert matcher.catalog_size > 0


def test_catalog_load_error_on_bad_path() -> None:
    m = CatalogMatcher(catalog_path="catalog/does_not_exist.json")
    with pytest.raises(CatalogLoadError):
        m.load()


def test_load_is_idempotent(matcher: CatalogMatcher) -> None:
    # Second load should not raise or change the size
    size_before = matcher.catalog_size
    matcher.load()
    assert matcher.catalog_size == size_before


# ---------------------------------------------------------------------------
# Exact match (case-insensitive)
# ---------------------------------------------------------------------------

def test_exact_match(matcher: CatalogMatcher) -> None:
    result = matcher.match("Python (New)")
    assert result is not None
    assert result.name == "Python (New)"


def test_exact_match_case_insensitive(matcher: CatalogMatcher) -> None:
    result = matcher.match("python (new)")
    assert result is not None
    assert result.name == "Python (New)"


def test_exact_match_all_caps(matcher: CatalogMatcher) -> None:
    result = matcher.match("PYTHON (NEW)")
    assert result is not None
    assert result.name == "Python (New)"


# ---------------------------------------------------------------------------
# Whitespace normalisation
# ---------------------------------------------------------------------------

def test_whitespace_normalisation(matcher: CatalogMatcher) -> None:
    # Extra internal spaces should still match
    result = matcher.match("Python  (New)")
    assert result is not None
    assert result.name == "Python (New)"


def test_leading_trailing_whitespace(matcher: CatalogMatcher) -> None:
    result = matcher.match("  Python (New)  ")
    # normalise strips outer spaces via casefold + split
    assert result is not None
    assert result.name == "Python (New)"


# ---------------------------------------------------------------------------
# RapidFuzz fuzzy match (fallback)
# ---------------------------------------------------------------------------

def test_rapidfuzz_close_match(matcher: CatalogMatcher) -> None:
    # "Agile Software Developmnt" (typo) scores ~98 WRatio vs "Agile Software Development"
    result = matcher.match("Agile Software Developmnt")
    assert result is not None
    assert "Agile" in result.name


def test_rapidfuzz_opq_abbreviation(matcher: CatalogMatcher) -> None:
    # "OPQ User Report" should fuzzy-match to the real name
    result = matcher.match("OPQ User Report")
    assert result is not None
    assert "OPQ" in result.name


# ---------------------------------------------------------------------------
# Threshold rejection — never guess
# ---------------------------------------------------------------------------

def test_no_match_below_threshold(matcher: CatalogMatcher) -> None:
    result = matcher.match("Rust Programming Assessment XYZ")
    assert result is None


def test_no_match_completely_unknown(matcher: CatalogMatcher) -> None:
    result = matcher.match("Zyxwvutsrqponmlkji Assessment")
    assert result is None


def test_no_match_short_garbage(matcher: CatalogMatcher) -> None:
    result = matcher.match("xyz")
    assert result is None


# ---------------------------------------------------------------------------
# ComparisonAssessment field population
# ---------------------------------------------------------------------------

def test_matched_record_has_all_fields(matcher: CatalogMatcher) -> None:
    result = matcher.match("Python (New)")
    assert result is not None
    assert result.entity_id != ""
    assert result.url.startswith("http")
    assert isinstance(result.job_levels, list)
    assert isinstance(result.languages, list)
    assert isinstance(result.keys, list)


# ---------------------------------------------------------------------------
# match_many — ordering preserved
# ---------------------------------------------------------------------------

def test_match_many_ordering(matcher: CatalogMatcher) -> None:
    names = ["Python (New)", "Agile Software Development"]
    matched, unmatched = matcher.match_many(names)
    assert len(matched) == 2
    assert matched[0].name == "Python (New)"
    assert matched[1].name == "Agile Software Development"
    assert unmatched == []


def test_match_many_partial_match(matcher: CatalogMatcher) -> None:
    names = ["Python (New)", "Rust Assessment That Does Not Exist"]
    matched, unmatched = matcher.match_many(names)
    assert len(matched) == 1
    assert matched[0].name == "Python (New)"
    assert "Rust Assessment That Does Not Exist" in unmatched


def test_match_many_all_unmatched(matcher: CatalogMatcher) -> None:
    names = ["Fake Assessment Alpha", "Fake Assessment Beta"]
    matched, unmatched = matcher.match_many(names)
    assert matched == []
    assert set(unmatched) == set(names)


def test_match_many_preserves_unmatched_original_name(matcher: CatalogMatcher) -> None:
    original = "My Custom Non-Existent Test 9999"
    _, unmatched = matcher.match_many([original])
    assert unmatched[0] == original


# ---------------------------------------------------------------------------
# Duplicates in input
# ---------------------------------------------------------------------------

def test_duplicate_names_both_resolved(matcher: CatalogMatcher) -> None:
    # Duplicates should each match — caller decides dedup
    names = ["Python (New)", "Python (New)"]
    matched, unmatched = matcher.match_many(names)
    assert len(matched) == 2
    assert matched[0].name == matched[1].name == "Python (New)"
