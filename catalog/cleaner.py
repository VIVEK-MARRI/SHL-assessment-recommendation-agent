"""Deterministic catalog cleaning utilities."""

from __future__ import annotations

import unicodedata
from typing import Any, cast
from urllib.parse import urlparse, urlunparse

from catalog.constants import (
    BOOLEAN_FALSE_VALUES,
    BOOLEAN_TRUE_VALUES,
    DEFAULT_URL_SCHEME,
    INVISIBLE_CHARS_PATTERN,
    LIST_SPLIT_PATTERN,
    WHITESPACE_PATTERN,
)


def clean_text(value: str) -> str:
    """Clean text deterministically without changing semantic meaning.

    Args:
        value: Raw input text.

    Returns:
        Cleaned text with normalized unicode and whitespace.
    """
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    normalized = INVISIBLE_CHARS_PATTERN.sub("", normalized)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    normalized = WHITESPACE_PATTERN.sub(" ", normalized)
    return normalized.strip()


def clean_url(value: str) -> str:
    """Normalize URL string formatting deterministically.

    Args:
        value: Raw URL string.

    Returns:
        Normalized URL string.
    """
    cleaned = clean_text(value)
    if cleaned.startswith("www."):
        cleaned = f"{DEFAULT_URL_SCHEME}://{cleaned}"

    parsed = urlparse(cleaned)
    if not parsed.scheme and parsed.netloc == "" and "/" in parsed.path:
        cleaned = f"{DEFAULT_URL_SCHEME}://{cleaned}"
        parsed = urlparse(cleaned)
    elif not parsed.scheme and parsed.path:
        cleaned = f"{DEFAULT_URL_SCHEME}://{cleaned}"
        parsed = urlparse(cleaned)

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


def clean_boolean(value: bool | str | int) -> bool:
    """Normalize boolean-like values into strict booleans.

    Args:
        value: Raw boolean-like value.

    Returns:
        Normalized boolean value.

    Raises:
        ValueError: If value cannot be interpreted as boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
        raise ValueError("integer boolean values must be 0 or 1")
    if isinstance(value, str):
        cleaned = clean_text(value).lower()
        if cleaned in BOOLEAN_TRUE_VALUES:
            return True
        if cleaned in BOOLEAN_FALSE_VALUES:
            return False
    raise ValueError("value cannot be interpreted as boolean")


def clean_list(value: list[str] | str) -> list[str]:
    """Normalize list-like values from strings or list inputs.

    Args:
        value: Raw list-like data.

    Returns:
        Deterministically cleaned list of unique values preserving order.

    Raises:
        ValueError: If input type is unsupported.
    """
    items: list[str]
    if isinstance(value, str):
        if not value.strip():
            return []
        items = LIST_SPLIT_PATTERN.split(value.strip())
    elif isinstance(value, list):
        items = [str(item) for item in value]
    else:
        raise ValueError("list fields must be string or list")

    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = clean_text(item)
        if not cleaned:
            continue
        marker = cleaned.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        output.append(cleaned)
    return output


def clean_record(record: dict[str, object]) -> dict[str, object]:
    """Apply deterministic cleaning rules to a raw assessment record.

    Args:
        record: Raw record dictionary.

    Returns:
        Cleaned record dictionary.

    Raises:
        ValueError: If expected field types are invalid.
    """
    cleaned: dict[str, object] = {}

    for field in ("entity_id", "name", "description", "status", "duration", "duration_raw"):
        raw = record.get(field)
        cleaned[field] = clean_text(str(raw)) if raw is not None else ""

    raw_jl = record.get("job_levels_raw")
    cleaned["job_levels_raw"] = clean_text(str(raw_jl)) if raw_jl is not None else ""

    raw_lang = record.get("languages_raw")
    cleaned["languages_raw"] = clean_text(str(raw_lang)) if raw_lang is not None else ""

    raw_link = record.get("link")
    cleaned["link"] = clean_url(str(raw_link)) if raw_link is not None else ""

    keys = record.get("keys")
    cleaned["keys"] = clean_list(cast(Any, keys) if keys is not None else [])

    jls = record.get("job_levels")
    cleaned["job_levels"] = clean_list(cast(Any, jls) if jls is not None else [])

    langs = record.get("languages")
    cleaned["languages"] = clean_list(cast(Any, langs) if langs is not None else [])

    remote = record.get("remote")
    cleaned["remote"] = clean_boolean(cast(Any, remote) if remote is not None else False)

    adaptive = record.get("adaptive")
    cleaned["adaptive"] = clean_boolean(cast(Any, adaptive) if adaptive is not None else False)

    return cleaned
