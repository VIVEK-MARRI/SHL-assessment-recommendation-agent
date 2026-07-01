from __future__ import annotations

import logging
from time import perf_counter

from agent.catalog_validator import CatalogValidator
from agent.generation_models import LLMGenerationResult
from agent.validator_models import ValidatedGenerationResult

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Base exception for Response Validator failures."""

class CatalogValidationError(ValidationError):
    """Raised when catalog validation logic fails internally."""

class InvalidGenerationResult(ValidationError):
    """Raised when the LLM result structurally violates rules (e.g. empty reply)."""


class ResponseValidator:
    """Validates LLMGenerationResult against the catalog and structural rules."""

    def __init__(self, catalog_validator: CatalogValidator | None = None) -> None:
        self._catalog = catalog_validator or CatalogValidator()

    def validate(self, result: LLMGenerationResult) -> ValidatedGenerationResult:
        """
        Validates the generation result.
        Returns a ValidatedGenerationResult.
        Raises InvalidGenerationResult if unrecoverable rules are violated.
        """
        started = perf_counter()
        
        # Rule 1: Reply must not be empty
        if not result.reply.strip():
            raise InvalidGenerationResult("LLM reply is empty.")
            
        # Rule 2: recommended_names must be 0 to 10 items (never 11+)
        if len(result.recommended_names) > 10:
            raise InvalidGenerationResult(f"LLM returned too many recommendations: {len(result.recommended_names)}")
            
        # Rule 3, 4, 5, 6: Validate names against catalog, dedup, extract invalid
        valid, invalid = self._catalog.validate_names(result.recommended_names)
        
        # Rule 7 & 8: Determine validation_passed
        validation_errors = []
        if invalid:
            validation_errors.append(f"Invalid assessment names returned: {', '.join(invalid)}")
            
        if result.recommended_names and not valid:
            # Rule 7: If ALL recommendations are invalid
            validation_passed = False
        else:
            # Rule 8 (and 0 recs): If some are valid, or 0 recommendations to begin with
            validation_passed = True
            
        elapsed_ms = (perf_counter() - started) * 1000
        
        logger.info(
            "Validation completed: valid=%d rejected=%d latency_ms=%.2f passed=%s",
            len(valid),
            len(invalid),
            elapsed_ms,
            validation_passed
        )
        if invalid:
            logger.warning("Rejected assessment names: %s", invalid)
            
        # Rule 9: Never modify reply
        return ValidatedGenerationResult(
            reply=result.reply,
            validated_names=valid,
            invalid_names=invalid,
            end_of_conversation=result.end_of_conversation,
            validation_passed=validation_passed,
            validation_errors=validation_errors
        )
