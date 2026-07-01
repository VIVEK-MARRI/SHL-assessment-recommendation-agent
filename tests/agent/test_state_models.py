"""Unit tests for agent conversation state models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.conversation_models import ConversationMessage, ConversationState


def test_conversation_message_accepts_user_and_assistant() -> None:
    user = ConversationMessage(role="user", content=" Need a Java assessment ")
    assistant = ConversationMessage(role="assistant", content="Sure")

    assert user.content == "Need a Java assessment"
    assert assistant.role == "assistant"


def test_conversation_message_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        ConversationMessage(role="system", content="hidden")


def test_conversation_message_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        ConversationMessage(role="user", content="   ")


def test_state_defaults_missing_fields() -> None:
    state = ConversationState.model_validate({})

    assert state.scope_flag == "in_scope"
    assert state.technical_skills == []
    assert state.leadership_required is False
    assert state.clarification_needed is False


def test_state_normalizes_lists_deterministically() -> None:
    state = ConversationState.model_validate(
        {
            "technical_skills": [" Java ", "java", "", "Spring"],
            "missing_information": None,
        }
    )

    assert state.technical_skills == ["Java", "Spring"]
    assert state.missing_information == []


def test_state_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ConversationState.model_validate({"retrieved_assessments": []})

