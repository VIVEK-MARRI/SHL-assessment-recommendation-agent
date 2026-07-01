"""Conversation state extraction orchestration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from time import perf_counter
from typing import Protocol

from pydantic import ValidationError

from agent.conversation_models import ConversationMessage, ConversationState
from agent.llm_client import LLMClient, LLMConnectionError, LLMResponseError

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "state_extraction_prompt.txt"


class StateExtractionError(Exception):
    """Raised when conversation state extraction cannot be completed."""


class JSONParseError(StateExtractionError):
    """Raised when LLM JSON cannot be parsed or validated."""


class StateExtractionLLM(Protocol):
    """Protocol implemented by LLM clients used for state extraction."""

    def complete_json(self, system_prompt: str, user_payload: str) -> str:
        """Return raw JSON text for the extraction request."""


class StateExtractor:
    """Extract ``ConversationState`` from complete conversation history."""

    def __init__(
        self,
        llm_client: StateExtractionLLM | None = None,
        prompt_path: Path = PROMPT_PATH,
        max_parse_retries: int = 1,
    ) -> None:
        """Create a state extractor with injectable LLM dependency."""
        if max_parse_retries < 0:
            raise StateExtractionError("max_parse_retries must be non-negative")
        self._llm_client = llm_client or LLMClient()
        self._prompt_path = prompt_path
        self._max_parse_retries = max_parse_retries

    def extract(self, messages: list[ConversationMessage | dict[str, str]]) -> ConversationState:
        """Extract deterministic structured state from complete conversation history."""
        started_at = perf_counter()
        try:
            parsed_messages = [ConversationMessage.model_validate(message) for message in messages]
        except ValidationError as exc:
            raise StateExtractionError("messages did not match ConversationMessage") from exc
        if not parsed_messages:
            raise StateExtractionError("messages must contain at least one conversation message")

        system_prompt = self._load_system_prompt()
        user_payload = self._build_user_payload(parsed_messages)
        logger.info("Conversation length: messages=%d", len(parsed_messages))

        last_error: Exception | None = None
        for attempt in range(self._max_parse_retries + 1):
            try:
                logger.info("LLM request started: attempt=%d", attempt + 1)
                raw_response = self._llm_client.complete_json(system_prompt, user_payload)
                logger.info(
                    "LLM request completed: attempt=%d chars=%d",
                    attempt + 1,
                    len(raw_response),
                )
                state = self._parse_state(raw_response)
                elapsed_ms = (perf_counter() - started_at) * 1000
                logger.info(
                    "Validation successful: elapsed_ms=%.2f attempt=%d",
                    elapsed_ms,
                    attempt + 1,
                )
                return state
            except (JSONParseError, ValidationError) as exc:
                last_error = exc
                logger.error("State extraction parse error: attempt=%d error=%s", attempt + 1, exc)
                if attempt >= self._max_parse_retries:
                    raise JSONParseError(
                        "LLM response could not be parsed as ConversationState"
                    ) from exc
            except (LLMConnectionError, LLMResponseError):
                logger.exception("State extraction LLM error")
                raise

        raise StateExtractionError("State extraction failed") from last_error

    def _load_system_prompt(self) -> str:
        try:
            prompt = self._prompt_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise StateExtractionError(f"State extraction prompt could not be read: {exc}") from exc
        if not prompt:
            raise StateExtractionError("State extraction prompt is empty")
        return prompt

    @staticmethod
    def _build_user_payload(messages: list[ConversationMessage]) -> str:
        payload = {
            "messages": [message.model_dump() for message in messages],
            "output_schema": ConversationState.model_json_schema(),
        }
        return json.dumps(payload, ensure_ascii=True, sort_keys=True)

    @staticmethod
    def _parse_state(raw_response: str) -> ConversationState:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise JSONParseError(f"LLM response was not valid JSON: {exc}") from exc
        logger.info("Parse successful")
        try:
            return ConversationState.model_validate(data)
        except ValidationError as exc:
            raise JSONParseError("LLM JSON did not match ConversationState") from exc


def extract_conversation_state(
    messages: list[ConversationMessage | dict[str, str]],
    llm_client: StateExtractionLLM | None = None,
) -> ConversationState:
    """Convenience function for one-off conversation state extraction."""
    return StateExtractor(llm_client=llm_client).extract(messages)
