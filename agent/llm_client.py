"""Configurable LLM client for structured JSON state extraction."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LLMConnectionError(Exception):
    """Raised when the configured LLM provider cannot be reached."""


class LLMResponseError(Exception):
    """Raised when the LLM provider returns an unusable response."""


@dataclass(frozen=True)
class LLMClientConfig:
    """Runtime configuration for the state extraction LLM client."""

    provider: str
    api_key: str
    model: str
    temperature: float = 0.0
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> LLMClientConfig:
        """Build client configuration from environment variables."""
        provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
        model = os.getenv("LLM_MODEL_CONVERSATION_STATE", "").strip()
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            default_model = "llama-3.1-8b-instant"
        elif provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            default_model = "openai/gpt-4o-mini"
        else:
            raise LLMResponseError("LLM_PROVIDER must be 'groq' or 'openrouter'")

        if not api_key:
            env_name = "GROQ_API_KEY" if provider == "groq" else "OPENROUTER_API_KEY"
            raise LLMResponseError(f"{env_name} is required for LLM_PROVIDER={provider}")

        return cls(
            provider=provider,
            api_key=api_key,
            model=model or default_model,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )


class LLMClient:
    """HTTP client for Groq and OpenRouter chat-completion JSON responses."""

    def __init__(
        self,
        config: LLMClientConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create an LLM client with injectable configuration and transport."""
        self._config = config or LLMClientConfig.from_env()
        self._http_client = http_client

    def complete_json(self, system_prompt: str, user_payload: str) -> str:
        """Return raw JSON text from one LLM chat-completion request."""
        payload = {
            "model": self._config.model,
            "temperature": self._config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "LLM request started: provider=%s model=%s",
            self._config.provider,
            self._config.model,
        )
        try:
            response = self._request(payload=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise LLMConnectionError(f"LLM request failed: {exc}") from exc

        if response.status_code >= 400:
            raise LLMResponseError(
                f"LLM provider returned status {response.status_code}: {response.text[:500]}"
            )

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMResponseError("LLM response did not contain message content") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("LLM response content was empty")
        logger.info("LLM request completed: chars=%d", len(content))
        return content

    def _request(self, payload: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        url = self._endpoint_url()
        import time
        max_retries = 3
        for attempt in range(max_retries + 1):
            if self._http_client is not None:
                response = self._http_client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self._config.timeout_seconds,
                )
            else:
                with httpx.Client(timeout=self._config.timeout_seconds) as client:
                    response = client.post(url, json=payload, headers=headers)

            if response.status_code == 429 and attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Rate limited (429), retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                continue

            return response

    def _endpoint_url(self) -> str:
        if self._config.provider == "groq":
            return "https://api.groq.com/openai/v1/chat/completions"
        if self._config.provider == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        raise LLMResponseError("Unsupported LLM provider")
