from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

import httpx

from agent.llm_client import LLMClientConfig

logger = logging.getLogger(__name__)

class GenerationError(Exception):
    """Base exception for LLM Response Generation failures."""

class ProviderError(GenerationError):
    """Raised when the LLM provider fails."""

class JSONGenerationError(GenerationError):
    """Raised when the LLM response is not valid JSON or violates schema."""

class GenerationTimeoutError(ProviderError):
    """Raised when the LLM provider times out."""

class RateLimitError(ProviderError):
    """Raised when the LLM provider returns a 429 status."""


class GenerationClient:
    """HTTP client for Groq and OpenRouter specifically for final generation."""

    def __init__(
        self,
        config: LLMClientConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config or LLMClientConfig.from_env()
        self._http_client = http_client

    def generate(self, system_prompt: str, user_payload: str) -> dict[str, Any]:
        """Call the LLM and return the parsed JSON and metadata."""
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

        started_at = perf_counter()
        logger.info(
            "Generation request started: provider=%s model=%s",
            self._config.provider,
            self._config.model,
        )

        try:
            response = self._request(payload=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError(f"LLM request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"LLM request failed: {exc}") from exc

        elapsed_ms = (perf_counter() - started_at) * 1000

        if response.status_code == 429:
            raise RateLimitError("LLM provider rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"LLM provider error {response.status_code}: {response.text[:200]}")
        if response.status_code >= 400:
            raise ProviderError(f"LLM client error {response.status_code}: {response.text[:200]}")

        try:
            body = response.json()
        except Exception as exc:
            raise ProviderError("LLM provider did not return valid JSON wrapper") from exc

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "unknown")
            usage = body.get("usage", {})
            tokens_prompt = usage.get("prompt_tokens", 0)
            tokens_completion = usage.get("completion_tokens", 0)
            tokens_total = usage.get("total_tokens", 0)
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("LLM response did not contain expected message content") from exc

        if not isinstance(content, str) or not content.strip():
            raise JSONGenerationError("LLM response content was empty")
            
        logger.info(
            "Generation completed: provider=%s model=%s latency_ms=%.2f prompt_tokens=%d completion_tokens=%d finish_reason=%s",
            self._config.provider,
            self._config.model,
            elapsed_ms,
            tokens_prompt,
            tokens_completion,
            finish_reason
        )

        return {
            "content": content,
            "provider": self._config.provider,
            "model": self._config.model,
            "latency_ms": elapsed_ms,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "tokens_total": tokens_total,
            "finish_reason": finish_reason,
        }

    def _request(self, payload: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        url = self._endpoint_url()
        # Enforce 20s timeout per instructions
        timeout = 20.0 
        
        import time
        max_retries = 3
        for attempt in range(max_retries + 1):
            if self._http_client is not None:
                response = self._http_client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                with httpx.Client(timeout=timeout) as client:
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
        
        return response

    def _endpoint_url(self) -> str:
        if self._config.provider == "groq":
            return "https://api.groq.com/openai/v1/chat/completions"
        if self._config.provider == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        raise ProviderError("Unsupported LLM provider")
