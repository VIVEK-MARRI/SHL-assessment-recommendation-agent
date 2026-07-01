"""Typed application settings loaded from environment variables.

This module is the single source of configuration values for all packages.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Strongly typed runtime settings for the service foundation.

    All modules must consume settings through this model instead of reading
    environment variables directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")
    app_name: str = Field(default="shl-assessment-recommendation-agent", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT", ge=1, le=65535)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    log_file: str = Field(default="app.log", alias="LOG_FILE")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model_conversation_state: str = Field(
        default="gpt-4o-mini", alias="LLM_MODEL_CONVERSATION_STATE"
    )
    llm_model_response: str = Field(default="gpt-4o-mini", alias="LLM_MODEL_RESPONSE")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE", ge=0.0, le=2.0)
    llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS", ge=1, le=300)
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES", ge=0, le=10)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    catalog_path: str = Field(default="catalog/validated_catalog.json", alias="CATALOG_PATH")

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL_NAME"
    )
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(default=64, alias="EMBEDDING_BATCH_SIZE", ge=1)
    bm25_index_path: str = Field(default="retrieval/indexes/bm25.pkl", alias="BM25_INDEX_PATH")
    faiss_index_path: str = Field(
        default="retrieval/indexes/faiss.index", alias="FAISS_INDEX_PATH"
    )
    top_k_bm25: int = Field(default=20, alias="TOP_K_BM25", ge=1)
    top_k_embedding: int = Field(default=20, alias="TOP_K_EMBEDDING", ge=1)
    rrf_k: int = Field(default=60, alias="RRF_K", ge=1)

    min_retrieval_confidence: float = Field(
        default=0.35, alias="MIN_RETRIEVAL_CONFIDENCE", ge=0.0, le=1.0
    )
    min_recommendation_count: int = Field(default=1, alias="MIN_RECOMMENDATION_COUNT", ge=0)
    max_recommendation_count: int = Field(default=8, alias="MAX_RECOMMENDATION_COUNT", ge=1)

    eval_data_path: str = Field(default="eval/data", alias="EVAL_DATA_PATH")
    eval_output_path: str = Field(default="eval/output", alias="EVAL_OUTPUT_PATH")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Validate runtime environment identifier.

        Args:
            value: Environment name supplied from configuration.

        Returns:
            A normalized, validated environment name.

        Raises:
            ValueError: If value is not an accepted environment.
        """
        normalized = value.strip().lower()
        allowed = {"development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {sorted(allowed)}")
        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate logging level.

        Args:
            value: Proposed log level value.

        Returns:
            Upper-cased level accepted by ``logging``.

        Raises:
            ValueError: If value is not a valid standard log level.
        """
        normalized = value.strip().upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return normalized

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key_for_provider(cls, value: str, info: ValidationInfo) -> str:
        """Ensure required API keys are present for configured provider.

        Args:
            value: API key value from environment.
            info: Validation context with sibling fields.

        Returns:
            The original API key value.

        Raises:
            ValueError: If provider requires an API key but none is set.
        """
        provider = str(info.data.get("llm_provider", "")).strip().lower()
        if provider == "openai" and not value.strip():
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return value

    @field_validator(
        "catalog_path",
        "log_dir",
        "eval_data_path",
        "eval_output_path",
        "bm25_index_path",
        "faiss_index_path",
    )
    @classmethod
    def normalize_paths(cls, value: str) -> str:
        """Normalize path-style settings to POSIX-like strings.

        Args:
            value: Input path string.

        Returns:
            Normalized path string.
        """
        return Path(value).as_posix()

    @field_validator("max_recommendation_count")
    @classmethod
    def validate_recommendation_bounds(cls, value: int, info: ValidationInfo) -> int:
        """Validate recommendation count boundaries.

        Args:
            value: Maximum recommendation count.
            info: Validation context with sibling fields.

        Returns:
            Valid maximum recommendation count.

        Raises:
            ValueError: If max recommendations is less than configured minimum.
        """
        min_count = int(info.data.get("min_recommendation_count", 0))
        if value < min_count:
            raise ValueError("MAX_RECOMMENDATION_COUNT must be >= MIN_RECOMMENDATION_COUNT")
        return value


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings instance.

    Returns:
        Initialized and validated application settings.
    """
    return AppSettings()
