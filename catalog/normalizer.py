"""Deterministic normalization for cleaned catalog records."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from catalog.constants import CATEGORY_ALIASES, JOB_LEVEL_ALIASES, LANGUAGE_ALIASES, STATUS_ALIASES
from catalog.cleaner import clean_text


def normalize_category(value: str) -> str:
    """Normalize category names to canonical forms.

    Args:
        value: Category string.

    Returns:
        Canonical category string when mapped, otherwise cleaned input.
    """
    cleaned = clean_text(value)
    alias_key = cleaned.casefold()
    return CATEGORY_ALIASES.get(alias_key, cleaned)


def normalize_language(value: str) -> str:
    """Normalize language values deterministically.

    Args:
        value: Language string.

    Returns:
        Canonical language string when mapped, otherwise cleaned input.
    """
    cleaned = clean_text(value)
    alias_key = cleaned.casefold()
    return LANGUAGE_ALIASES.get(alias_key, cleaned)


def normalize_job_level(value: str) -> str:
    """Normalize job level values deterministically.

    Args:
        value: Job level string.

    Returns:
        Canonical job level string when mapped, otherwise cleaned input.
    """
    cleaned = clean_text(value)
    alias_key = cleaned.casefold()
    return JOB_LEVEL_ALIASES.get(alias_key, cleaned)


def normalize_status(value: str) -> str:
    """Normalize status values to canonical representation.

    Args:
        value: Raw status value.

    Returns:
        Canonical status if mapped, otherwise lower-cased cleaned value.
    """
    cleaned = clean_text(value).casefold()
    return STATUS_ALIASES.get(cleaned, cleaned)


def normalize_url(value: str) -> str:
    """Normalize URL casing and strip fragments.

    Args:
        value: Cleaned URL string.

    Returns:
        Canonicalized URL string.
    """
    parsed = urlparse(value)
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
    )
    path = normalized.path or ""
    if path != "/":
        path = path.rstrip("/")
    normalized = normalized._replace(path=path)
    return urlunparse(normalized)


def normalize_record(record: dict[str, object]) -> dict[str, object]:
    """Normalize all supported fields in a cleaned assessment record.

    Args:
        record: Cleaned record dictionary.

    Returns:
        Normalized record dictionary.
    """
    normalized = dict(record)

    from typing import cast, Any
    normalized["keys"] = [normalize_category(value) for value in cast(Any, record.get("keys", []))]
    normalized["languages"] = [
        normalize_language(value) for value in cast(Any, record.get("languages", []))
    ]
    normalized["job_levels"] = [
        normalize_job_level(value) for value in cast(Any, record.get("job_levels", []))
    ]
    normalized["status"] = normalize_status(str(record.get("status", "")))
    normalized["link"] = normalize_url(str(record.get("link", "")))

    return normalized
