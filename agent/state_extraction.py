"""Conversation state extraction orchestration."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from time import perf_counter
from typing import Protocol

from pydantic import ValidationError

from agent.conversation_models import ConversationMessage, ConversationState
from agent.llm_client import LLMClient, LLMConnectionError, LLMResponseError

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "state_extraction_prompt.txt"

# Deterministic overwrite detection — used as safety net after LLM extraction
_OVERWRITE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bactually\b", re.IGNORECASE),
    re.compile(r"\binstead\b", re.IGNORECASE),
    re.compile(r"\brather\b", re.IGNORECASE),
    re.compile(r"\bchange\b", re.IGNORECASE),
    re.compile(r"\bswitch\b", re.IGNORECASE),
    re.compile(r"\bupdate\b", re.IGNORECASE),
    re.compile(r"\bmodified?\b", re.IGNORECASE),
    re.compile(r"\b(we|i)\s+(now\s+)?need\b", re.IGNORECASE),
    re.compile(r"\bmoving\s+to\b", re.IGNORECASE),
    re.compile(r"\bno\s+(longer|more)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+anymore\b", re.IGNORECASE),
    re.compile(r"\bremove\b", re.IGNORECASE),
    re.compile(r"\b(drop|replace|substitute)\b", re.IGNORECASE),
]


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
                # Deterministic overwrite safety net
                state = self._apply_overwrite_safety_net(state, parsed_messages)
                elapsed_ms = (perf_counter() - started_at) * 1000
                logger.info(
                    "Validation successful: elapsed_ms=%.2f attempt=%d",
                    elapsed_ms,
                    attempt + 1,
                )
                print("====== DEBUG EXTRACTION ======")
                print("ConversationState:", state.model_dump())
                print("==============================")
                logger.debug("Raw LLM response: %s", raw_response)
                logger.debug("ConversationState: %s", state.model_dump())
                return state
            except (JSONParseError, ValidationError) as exc:
                last_error = exc
                logger.error("State extraction parse error: attempt=%d error=%s", attempt + 1, exc)
                if attempt >= self._max_parse_retries:
                    raise JSONParseError(
                        "LLM response could not be parsed as ConversationState"
                    ) from exc
                system_prompt = (
                    f"{system_prompt}\n\nThe previous JSON did not match the required schema.\n"
                    "Your JSON output MUST exactly match this structure:\n"
                    "{\n"
                    '  "role": null,\n'
                    '  "seniority": null,\n'
                    '  "technical_skills": [],\n'
                    '  "soft_skills": [],\n'
                    '  "leadership_required": false,\n'
                    '  "personality_required": false,\n'
                    '  "cognitive_required": false,\n'
                    '  "simulation_required": false,\n'
                    '  "constraints": [],\n'
                    '  "mentioned_assessment_names": [],\n'
                    '  "comparison_requested": false,\n'
                    '  "scope_flag": "in_scope",\n'
                    '  "conversation_goal": null,\n'
                    '  "clarification_needed": false,\n'
                    '  "missing_information": [],\n'
                    '  "reasoning_summary": "",\n'
                    '  "refinement_detected": false\n'
                    "}\n"
                    "Do not include any additional keys. Do not include technical_skills_required."
                )
            except LLMResponseError as exc:
                if "400" in str(exc) and "json_validate_failed" in str(exc):
                    last_error = exc
                    logger.error("LLM provider rejected generated JSON on attempt=%d: %s", attempt + 1, exc)
                    if attempt >= self._max_parse_retries:
                        raise JSONParseError("LLM response was repeatedly malformed") from exc
                    system_prompt = (
                        f"{system_prompt}\n\nThe previous JSON did not match the required schema.\n"
                        "Your JSON output MUST exactly match this structure:\n"
                        "{\n"
                        '  "role": null,\n'
                        '  "seniority": null,\n'
                        '  "technical_skills": [],\n'
                        '  "soft_skills": [],\n'
                        '  "leadership_required": false,\n'
                        '  "personality_required": false,\n'
                        '  "cognitive_required": false,\n'
                        '  "simulation_required": false,\n'
                        '  "constraints": [],\n'
                        '  "mentioned_assessment_names": [],\n'
                        '  "comparison_requested": false,\n'
                        '  "scope_flag": "in_scope",\n'
                        '  "conversation_goal": null,\n'
                        '  "clarification_needed": false,\n'
                        '  "missing_information": [],\n'
                        '  "reasoning_summary": "",\n'
                        '  "refinement_detected": false\n'
                        "}\n"
                        "Do not include any additional keys. Do not include technical_skills_required."
                    )
                else:
                    logger.exception("State extraction LLM error")
                    raise
            except LLMConnectionError:
                logger.exception("State extraction LLM connection error")
                raise

        raise StateExtractionError("State extraction failed") from last_error

    @staticmethod
    def _apply_overwrite_safety_net(
        state: ConversationState,
        messages: list[ConversationMessage],
    ) -> ConversationState:
        """Deterministic post-processing to ensure state overwrite.

        If the last user message contains overwrite indicators (actually, instead, etc.),
        remove any technical_skills or role that were mentioned in EARLIER user messages
        but NOT in the last user message. This catches LLM accumulation errors.
        """
        if len(messages) < 2:
            return state

        # Find the last user message
        last_user_msg: str | None = None
        earlier_user_contents: list[str] = []
        for msg in messages:
            if msg.role == "user":
                if last_user_msg is not None:
                    earlier_user_contents.append(last_user_msg)
                last_user_msg = msg.content

        if last_user_msg is None:
            return state

        # Check if the last message indicates an overwrite/change
        has_overwrite = any(p.search(last_user_msg) for p in _OVERWRITE_PATTERNS)
        if not has_overwrite:
            return state

        # Tokenize the last message and earlier messages
        # Strip trailing/leading dots so sentence punctuation doesn't affect matching
        last_tokens = set(re.findall(r"[a-zA-Z0-9+#.]+", last_user_msg.casefold()))
        last_tokens = {t.strip(".") for t in last_tokens}
        earlier_tokens: set[str] = set()
        for content in earlier_user_contents:
            tokens = re.findall(r"[a-zA-Z0-9+#.]+", content.casefold())
            earlier_tokens.update(t.strip(".") for t in tokens)

        # Find skills that were mentioned in earlier messages but NOT in the last message
        stale_skills: list[str] = []
        for skill in state.technical_skills:
            skill_tokens = set(re.findall(r"[a-zA-Z0-9+#.]+", skill.casefold()))
            if skill_tokens and skill_tokens <= earlier_tokens and not skill_tokens & last_tokens:
                stale_skills.append(skill)

        # Find role tokens that conflict with last message
        staled_role = False
        if state.role:
            role_tokens = set(re.findall(r"[a-zA-Z0-9+#.]+", state.role.casefold()))
            if role_tokens and role_tokens <= earlier_tokens and not role_tokens & last_tokens:
                # Only clear role if the last message defines a new role
                if any(t in last_tokens for t in {"developer", "engineer", "analyst", "manager", "lead", "specialist", "architect", "administrator", "scientist", "intern", "graduate"}):
                    staled_role = True

        if stale_skills or staled_role:
            logger.info(
                "Overwrite safety net: removing stale skills=%r stale_role=%s",
                stale_skills,
                staled_role,
            )
            updates: dict[str, object] = {}
            if stale_skills:
                updates["technical_skills"] = [s for s in state.technical_skills if s not in stale_skills]
            if staled_role:
                updates["role"] = None
            state = state.model_copy(update=updates)

        return state

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
            # Strip markdown JSON wrapping if present
            clean_response = raw_response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            data = json.loads(clean_response)
        except json.JSONDecodeError as exc:
            raise JSONParseError(f"LLM response was not valid JSON: {exc}") from exc
        logger.info("Parse successful")
        logger.debug("Raw LLM state: %s", raw_response)
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
