from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Recommendation(BaseModel):
    """A single SHL assessment in the final API response."""

    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    test_type: list[str]


class ChatResponse(BaseModel):
    """The final response returned to the user."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    recommendations: Optional[list[Recommendation]] = None
