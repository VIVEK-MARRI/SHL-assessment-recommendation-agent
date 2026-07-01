import pytest
from unittest.mock import MagicMock

from agent.catalog_validator import CatalogValidator
from agent.generation_models import LLMGenerationResult
from agent.validator import InvalidGenerationResult, ResponseValidator

@pytest.fixture
def mock_catalog() -> CatalogValidator:
    catalog = MagicMock(spec=CatalogValidator)
    def fake_validate_names(names):
        valid = []
        invalid = []
        seen = set()
        for n in names:
            n_clean = n.strip()
            n_lower = n_clean.lower()
            if n_lower in seen:
                continue
            seen.add(n_lower)
            if n_lower in ["valid1", "valid2"]:
                valid.append(n_clean) # Mock canonicalization
            else:
                invalid.append(n_clean)
        return valid, invalid
    
    catalog.validate_names.side_effect = fake_validate_names
    return catalog

def test_empty_reply(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="   ",
        recommended_names=["valid1"],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    with pytest.raises(InvalidGenerationResult) as exc:
        validator.validate(result)
    assert "empty" in str(exc.value)

def test_too_many_recommendations(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Here",
        recommended_names=[f"test{i}" for i in range(11)],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    with pytest.raises(InvalidGenerationResult) as exc:
        validator.validate(result)
    assert "too many" in str(exc.value)

def test_valid_recommendations(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Here",
        recommended_names=["valid1", "valid2"],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    validated = validator.validate(result)
    assert validated.reply == "Here"
    assert validated.validated_names == ["valid1", "valid2"]
    assert validated.invalid_names == []
    assert validated.validation_passed is True

def test_mixed_recommendations(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Here",
        recommended_names=["valid1", "invalid1", "valid2"],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    validated = validator.validate(result)
    assert validated.validated_names == ["valid1", "valid2"]
    assert validated.invalid_names == ["invalid1"]
    assert validated.validation_passed is True

def test_all_invalid(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Here",
        recommended_names=["invalid1", "invalid2"],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    validated = validator.validate(result)
    assert validated.validated_names == []
    assert validated.invalid_names == ["invalid1", "invalid2"]
    assert validated.validation_passed is False

def test_duplicate_recommendations(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Here",
        recommended_names=["valid1", "VALID1", "invalid1", "invalid1"],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    validated = validator.validate(result)
    assert validated.validated_names == ["valid1"]
    assert validated.invalid_names == ["invalid1"]
    assert validated.validation_passed is True

def test_zero_recommendations(mock_catalog: CatalogValidator) -> None:
    validator = ResponseValidator(catalog_validator=mock_catalog)
    result = LLMGenerationResult(
        reply="Clarifying question",
        recommended_names=[],
        provider="p", model="m", latency_ms=1, tokens_prompt=1, tokens_completion=1, tokens_total=2, finish_reason="stop"
    )
    validated = validator.validate(result)
    assert validated.validated_names == []
    assert validated.invalid_names == []
    assert validated.validation_passed is True
