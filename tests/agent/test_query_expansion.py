"""Unit tests for query_expansion.py — role expansion and skill normalisation."""

from __future__ import annotations

import pytest

from agent.query_expansion import (
    ROLE_EXPANSION,
    SKILL_NORMALIZATIONS,
    get_role_expansion,
    normalise_skill,
    normalise_skills,
)


# ---------------------------------------------------------------------------
# get_role_expansion — exact matches
# ---------------------------------------------------------------------------


def test_backend_developer_exact() -> None:
    terms = get_role_expansion("Backend Developer")
    assert "backend" in terms
    assert "api" in terms
    assert "database" in terms


def test_python_developer_exact() -> None:
    terms = get_role_expansion("Python Developer")
    assert "python" in terms
    assert "django" in terms
    assert "flask" in terms


def test_sales_manager_exact() -> None:
    terms = get_role_expansion("Sales Manager")
    assert "sales" in terms
    assert "leadership" in terms
    assert "negotiation" in terms


def test_data_scientist_exact() -> None:
    terms = get_role_expansion("Data Scientist")
    assert "machine learning" in terms
    assert "python" in terms
    assert "statistics" in terms


def test_engineering_manager_exact() -> None:
    terms = get_role_expansion("Engineering Manager")
    assert "leadership" in terms
    assert "management" in terms
    assert "mentoring" in terms


# ---------------------------------------------------------------------------
# get_role_expansion — case-insensitive
# ---------------------------------------------------------------------------


def test_role_expansion_case_insensitive() -> None:
    lower = get_role_expansion("backend developer")
    upper = get_role_expansion("BACKEND DEVELOPER")
    mixed = get_role_expansion("Backend Developer")
    assert lower == upper == mixed


# ---------------------------------------------------------------------------
# get_role_expansion — partial / substring matching
# ---------------------------------------------------------------------------


def test_partial_match_senior_python_developer() -> None:
    terms = get_role_expansion("Senior Python Developer")
    # Should match via "python developer" key
    assert "python" in terms


def test_partial_match_junior_backend_engineer() -> None:
    terms = get_role_expansion("Junior Backend Engineer")
    # Should match via "backend engineer" key
    assert "backend" in terms


# ---------------------------------------------------------------------------
# get_role_expansion — unknown role
# ---------------------------------------------------------------------------


def test_unknown_role_returns_empty() -> None:
    terms = get_role_expansion("Wizard of Light Bulb Moments")
    assert terms == []


def test_empty_role_returns_empty() -> None:
    assert get_role_expansion("") == []


# ---------------------------------------------------------------------------
# normalise_skill — specific aliases
# ---------------------------------------------------------------------------


def test_normalise_cpp() -> None:
    tokens = normalise_skill("C++")
    assert "C++" in tokens
    assert "cpp" in tokens


def test_normalise_csharp() -> None:
    tokens = normalise_skill("C#")
    assert "C#" in tokens
    assert "csharp" in tokens


def test_normalise_aspnet() -> None:
    tokens = normalise_skill("ASP.NET")
    assert "ASP.NET" in tokens
    assert "aspnet" in tokens


def test_normalise_nodejs() -> None:
    tokens = normalise_skill("Node.js")
    assert "Node.js" in tokens
    assert "nodejs" in tokens


def test_normalise_vuejs() -> None:
    tokens = normalise_skill("Vue.js")
    assert "Vue.js" in tokens
    assert "vuejs" in tokens


def test_normalise_machine_learning() -> None:
    tokens = normalise_skill("Machine Learning")
    assert "Machine Learning" in tokens
    assert "ml" in tokens


def test_normalise_ai() -> None:
    tokens = normalise_skill("Artificial Intelligence")
    assert "Artificial Intelligence" in tokens
    assert "ai" in tokens


def test_normalise_genai() -> None:
    tokens = normalise_skill("Generative AI")
    assert "Generative AI" in tokens
    assert "genai" in tokens


# ---------------------------------------------------------------------------
# normalise_skill — unknown skill keeps original only
# ---------------------------------------------------------------------------


def test_normalise_unknown_skill() -> None:
    tokens = normalise_skill("Python")
    assert tokens == ["Python"]
    assert len(tokens) == 1


def test_normalise_sql_no_alias() -> None:
    tokens = normalise_skill("SQL")
    assert tokens == ["SQL"]


# ---------------------------------------------------------------------------
# normalise_skills — deduplication
# ---------------------------------------------------------------------------


def test_normalise_skills_dedup() -> None:
    # "C++" expands to ["C++", "cpp"] — adding "cpp" again should not duplicate
    skills = ["C++", "cpp"]
    result = normalise_skills(skills)
    lower = [t.lower() for t in result]
    assert lower.count("cpp") == 1


def test_normalise_skills_preserves_order() -> None:
    skills = ["Python", "Machine Learning", "SQL"]
    first = normalise_skills(skills)
    second = normalise_skills(skills)
    assert first == second


def test_normalise_skills_all_included() -> None:
    skills = ["C++", "Node.js", "Python"]
    result = normalise_skills(skills)
    result_lower = [t.lower() for t in result]
    assert "cpp" in result_lower
    assert "nodejs" in result_lower
    assert "python" in result_lower
    assert "c++" in result_lower
    assert "node.js" in result_lower


# ---------------------------------------------------------------------------
# Sanity-check the static tables
# ---------------------------------------------------------------------------


def test_all_role_expansion_keys_are_lowercase() -> None:
    for key in ROLE_EXPANSION:
        assert key == key.lower(), f"Key not lowercase: {key!r}"


def test_all_skill_normalisation_keys_are_lowercase() -> None:
    for key in SKILL_NORMALIZATIONS:
        assert key == key.lower(), f"Key not lowercase: {key!r}"
