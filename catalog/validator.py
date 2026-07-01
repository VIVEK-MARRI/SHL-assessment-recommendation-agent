"""Validation and duplicate detection for catalog records."""

from __future__ import annotations

import time
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from config import get_logger

from catalog.constants import (
    ASSESSMENT_FIELD_ORDER,
    BOOLEAN_FIELDS,
    CANONICAL_STATUSES,
    REQUIRED_LIST_FIELDS,
    REQUIRED_STRING_FIELDS,
    URL_ALLOWED_SCHEMES,
)

logger = get_logger(__name__)


class CatalogValidationError(Exception):
    """Raised when catalog validation fails."""


class ValidationIssue(BaseModel):
    """Single validation issue for one record."""

    index: int
    field: str
    message: str


class ValidationReport(BaseModel):
    """Structured validation report for catalog processing."""

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    issues: list[ValidationIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0


def _is_valid_url(url_value: str) -> bool:
    """Check whether URL has allowed scheme and non-empty host.

    Args:
        url_value: URL string.

    Returns:
        True if valid, else False.
    """
    parsed = urlparse(url_value)
    return parsed.scheme.lower() in URL_ALLOWED_SCHEMES and bool(parsed.netloc)


def _canonical_url(url_value: str) -> str:
    """Generate canonical URL key for duplicate checks.

    Args:
        url_value: URL string.

    Returns:
        Canonical URL marker.
    """
    parsed = urlparse(url_value)
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"


def validate_record(record: dict[str, object], index: int) -> list[ValidationIssue]:
    """Validate one normalized catalog record.

    Args:
        record: Record to validate.
        index: Record index in source list.

    Returns:
        List of validation issues for the record.
    """
    issues: list[ValidationIssue] = []

    for field in REQUIRED_STRING_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(
                ValidationIssue(index=index, field=field, message="required non-empty string")
            )

    for field in REQUIRED_LIST_FIELDS:
        value = record.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            issues.append(ValidationIssue(index=index, field=field, message="required list[str]"))

    for field in BOOLEAN_FIELDS:
        value = record.get(field)
        if not isinstance(value, bool):
            issues.append(ValidationIssue(index=index, field=field, message="required bool"))

    link_value = record.get("link")
    if not isinstance(link_value, str) or not _is_valid_url(link_value):
        issues.append(ValidationIssue(index=index, field="link", message="invalid URL"))

    status_value = record.get("status")
    if isinstance(status_value, str) and status_value and status_value not in CANONICAL_STATUSES:
        issues.append(
            ValidationIssue(
                index=index,
                field="status",
                message=f"status must be one of {sorted(CANONICAL_STATUSES)}",
            )
        )

    for field in ASSESSMENT_FIELD_ORDER:
        if field not in record:
            issues.append(ValidationIssue(index=index, field=field, message="missing field"))

    return issues


def detect_duplicates(records: list[dict[str, object]]) -> list[ValidationIssue]:
    """Detect duplicate ids, names, and URLs.

    Args:
        records: Normalized records.

    Returns:
        Duplicate-related validation issues.
    """
    issues: list[ValidationIssue] = []

    seen_ids: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    seen_urls: dict[str, int] = {}

    for index, record in enumerate(records):
        entity_id = str(record.get("entity_id", "")).strip()
        name = str(record.get("name", "")).strip().casefold()
        link = str(record.get("link", "")).strip()

        if entity_id:
            if entity_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        index=index,
                        field="entity_id",
                        message=f"duplicate entity_id; first seen at index {seen_ids[entity_id]}",
                    )
                )
            else:
                seen_ids[entity_id] = index

        if name:
            if name in seen_names:
                issues.append(
                    ValidationIssue(
                        index=index,
                        field="name",
                        message=f"duplicate name; first seen at index {seen_names[name]}",
                    )
                )
            else:
                seen_names[name] = index

        if link:
            canonical_url = _canonical_url(link)
            if canonical_url in seen_urls:
                issues.append(
                    ValidationIssue(
                        index=index,
                        field="link",
                        message=f"duplicate URL; first seen at index {seen_urls[canonical_url]}",
                    )
                )
            else:
                seen_urls[canonical_url] = index

    return issues


def validate_records(records: list[dict[str, object]]) -> ValidationReport:
    """Validate normalized catalog records and produce report.

    Args:
        records: Normalized records.

    Returns:
        Validation report with issues and counts.

    Raises:
        CatalogValidationError: If record-level validation fails.
    """
    started = time.perf_counter()
    report = ValidationReport(total_records=len(records))

    for index, record in enumerate(records):
        record_issues = validate_record(record, index)
        report.issues.extend(record_issues)

    duplicate_issues = detect_duplicates(records)
    report.issues.extend(duplicate_issues)
    report.duplicate_records = len(duplicate_issues)

    invalid_indexes = {issue.index for issue in report.issues}
    report.invalid_records = len(invalid_indexes)
    report.valid_records = report.total_records - report.invalid_records
    report.elapsed_seconds = round(time.perf_counter() - started, 6)

    if report.issues:
        for issue in report.issues:
            logger.error("Validation failure: index=%s field=%s message=%s", issue.index, issue.field, issue.message)
    logger.info(
        "Catalog validation completed: total=%s valid=%s invalid=%s duplicates=%s elapsed=%ss",
        report.total_records,
        report.valid_records,
        report.invalid_records,
        report.duplicate_records,
        report.elapsed_seconds,
    )

    return report


def raise_if_invalid(report: ValidationReport) -> None:
    """Raise structured validation error when report has failures.

    Args:
        report: Validation report.

    Returns:
        None

    Raises:
        CatalogValidationError: If any issue is present.
    """
    if report.issues:
        raise CatalogValidationError(
            "Catalog validation failed: "
            f"invalid_records={report.invalid_records}, duplicate_records={report.duplicate_records}"
        )
