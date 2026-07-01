"""Shared constants for deterministic catalog management."""

from __future__ import annotations

import re
from pathlib import Path

RAW_CATALOG_DEFAULT_PATH = Path("catalog/raw_catalog.json")
CANONICAL_CATALOG_DEFAULT_PATH = Path("catalog/catalog.json")

ASSESSMENT_FIELD_ORDER: tuple[str, ...] = (
    "entity_id",
    "name",
    "link",
    "description",
    "keys",
    "job_levels",
    "job_levels_raw",
    "languages",
    "languages_raw",
    "duration",
    "duration_raw",
    "status",
    "remote",
    "adaptive",
)

REQUIRED_STRING_FIELDS: tuple[str, ...] = (
    "entity_id",
    "name",
    "link",
    "description",
    "status",
)

REQUIRED_LIST_FIELDS: tuple[str, ...] = (
    "keys",
    "job_levels",
    "languages",
)

BOOLEAN_FIELDS: tuple[str, ...] = ("remote", "adaptive")

URL_ALLOWED_SCHEMES: tuple[str, ...] = ("http", "https")
DEFAULT_URL_SCHEME = "https"

WHITESPACE_PATTERN = re.compile(r"\s+")
INVISIBLE_CHARS_PATTERN = re.compile(r"[\u200B-\u200D\u2060\uFEFF]")
LIST_SPLIT_PATTERN = re.compile(r"\s*[,;|]\s*")

BOOLEAN_TRUE_VALUES: set[str] = {
    "1",
    "t",
    "true",
    "yes",
    "y",
}
BOOLEAN_FALSE_VALUES: set[str] = {
    "0",
    "f",
    "false",
    "no",
    "n",
}

CATEGORY_CANONICAL_ORDER: tuple[str, ...] = (
    "Knowledge & Skills",
    "Personality & Behavior",
    "Ability & Aptitude",
    "Competencies",
    "Biodata & Situational Judgment",
    "Simulations",
    "Development & 360",
    "Assessment Exercises",
)

CATEGORY_ALIASES: dict[str, str] = {
    "knowledge and skills": "Knowledge & Skills",
    "knowledge & skills": "Knowledge & Skills",
    "personality and behavior": "Personality & Behavior",
    "personality & behavior": "Personality & Behavior",
    "ability and aptitude": "Ability & Aptitude",
    "ability & aptitude": "Ability & Aptitude",
    "competencies": "Competencies",
    "biodata and situational judgment": "Biodata & Situational Judgment",
    "biodata & situational judgment": "Biodata & Situational Judgment",
    "simulations": "Simulations",
    "development and 360": "Development & 360",
    "development & 360": "Development & 360",
    "assessment exercises": "Assessment Exercises",
}

KEY_TO_TEST_TYPE_MAP: dict[str, str] = {
    "Knowledge & Skills": "K",
    "Personality & Behavior": "P",
    "Ability & Aptitude": "A",
    "Competencies": "C",
    "Biodata & Situational Judgment": "B",
    "Simulations": "S",
    "Development & 360": "D",
    "Assessment Exercises": "E",
}

STATUS_ALIASES: dict[str, str] = {
    "ok": "active",
    "active": "active",
    "live": "active",
    "published": "active",
    "inactive": "inactive",
    "retired": "inactive",
    "archived": "inactive",
    "draft": "draft",
}

CANONICAL_STATUSES: set[str] = {"active", "inactive", "draft"}

LANGUAGE_ALIASES: dict[str, str] = {
    "english": "English",
    "en": "English",
    "english (usa)": "English (US)",
    "english us": "English (US)",
    "english uk": "English (UK)",
}

JOB_LEVEL_ALIASES: dict[str, str] = {
    "director": "Director",
    "entry-level": "Entry Level",
    "entry": "Entry Level",
    "entry level": "Entry Level",
    "executive": "Executive",
    "front line manager": "Front Line Manager",
    "graduate": "Graduate",
    "junior": "Entry Level",
    "general population": "General Population",
    "mid": "Mid Level",
    "mid level": "Mid Level",
    "mid-professional": "Mid Level",
    "professional individual contributor": "Professional Individual Contributor",
    "manager": "Manager",
    "senior": "Senior Level",
    "senior level": "Senior Level",
    "leadership": "Leadership",
    "supervisor": "Supervisor",
}
