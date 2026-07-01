"""Typed models for SHL Individual Test Solutions catalog records."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from catalog.constants import URL_ALLOWED_SCHEMES


class Assessment(BaseModel):
    """Canonical assessment record used throughout the system."""

    model_config = ConfigDict(extra="ignore")

    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    link: str = Field(min_length=1)
    description: str = Field(min_length=1)
    keys: list[str] = Field(default_factory=list)
    job_levels: list[str] = Field(default_factory=list)
    job_levels_raw: str = Field(default="")
    languages: list[str] = Field(default_factory=list)
    languages_raw: str = Field(default="")
    duration: str = Field(default="")
    duration_raw: str = Field(default="")
    status: str = Field(min_length=1)
    remote: bool
    adaptive: bool

    @field_validator("entity_id", "name", "description", "status")
    @classmethod
    def validate_non_blank_strings(cls, value: str) -> str:
        """Ensure required text values are present after trimming.

        Args:
            value: Incoming text value.

        Returns:
            Trimmed text value.

        Raises:
            ValueError: If resulting value is blank.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped

    @field_validator("keys", "job_levels", "languages")
    @classmethod
    def validate_lists(cls, values: list[str]) -> list[str]:
        """Validate list-based fields.

        Args:
            values: Input list values.

        Returns:
            Trimmed non-empty list values.

        Raises:
            ValueError: If list contains non-string values.
        """
        output: list[str] = []
        for value in values:
            if not isinstance(value, str):
                raise ValueError("list values must be strings")
            cleaned = value.strip()
            if cleaned:
                output.append(cleaned)
        return output

    @field_validator("link")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Validate that link is a valid absolute URL.

        Args:
            value: URL string.

        Returns:
            Trimmed URL string.

        Raises:
            ValueError: If URL is malformed.
        """
        url_value = value.strip()
        parsed = urlparse(url_value)
        if parsed.scheme.lower() not in URL_ALLOWED_SCHEMES or not parsed.netloc:
            raise ValueError("link must be a valid http or https URL")
        return url_value
