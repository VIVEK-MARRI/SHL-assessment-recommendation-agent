from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from agent.conversation_models import ConversationMessage


class ChatRequest(BaseModel):
    """Incoming chat request from the client."""

    messages: list[ConversationMessage] = Field(
        ...,
        description="The full conversation history. At least one message required.",
        examples=[
            [{"role": "user", "content": "I need a Python assessment for senior engineers."}]
        ],
    )
