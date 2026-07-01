"""Unit tests for deterministic catalog cleaning."""

from __future__ import annotations

from catalog.cleaner import clean_boolean, clean_list, clean_record, clean_text, clean_url


def test_clean_text_whitespace_and_newline_normalization() -> None:
    """Text cleaning should collapse whitespace and remove newlines."""
    assert clean_text("  Hello\n\nWorld   ") == "Hello World"


def test_clean_text_unicode_invisible_removed() -> None:
    """Text cleaning should remove zero-width characters."""
    assert clean_text("A\u200BB") == "AB"


def test_clean_url_normalization() -> None:
    """URL cleaning should normalize scheme/host and remove trailing slash."""
    assert clean_url(" WWW.SHL.COM/Path/ ") == "https://www.shl.com/Path"


def test_clean_boolean_string_values() -> None:
    """Boolean cleaning should parse supported string values."""
    assert clean_boolean("YES") is True
    assert clean_boolean("0") is False


def test_clean_list_string_and_deduplication() -> None:
    """List cleaning should split text and deduplicate values."""
    cleaned = clean_list(" English ; english | French ")
    assert cleaned == ["English", "French"]


def test_clean_record_normalizes_expected_fields() -> None:
    """Record cleaning should normalize key field families."""
    record = {
        "entity_id": "  SHL-1  ",
        "name": "  Example\nName ",
        "link": "www.shl.com/example/",
        "description": "  A\u200b description ",
        "keys": "Knowledge & Skills; Competencies",
        "job_levels": "Entry Level, Entry Level",
        "job_levels_raw": " Entry  Level ",
        "languages": ["English", " english "],
        "languages_raw": " English ",
        "duration": " 30 minutes ",
        "duration_raw": " 30 minutes ",
        "status": " Active ",
        "remote": "true",
        "adaptive": "false",
    }

    cleaned = clean_record(record)

    assert cleaned["entity_id"] == "SHL-1"
    assert cleaned["name"] == "Example Name"
    assert cleaned["description"] == "A description"
    assert cleaned["remote"] is True
    assert cleaned["adaptive"] is False
    assert cleaned["job_levels"] == ["Entry Level"]
