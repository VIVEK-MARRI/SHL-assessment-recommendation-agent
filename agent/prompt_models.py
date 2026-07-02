from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from agent.routing_models import RouteType

class GroundingAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    description: str = ""
    duration: str = ""
    job_levels: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    remote: bool = False
    adaptive: bool = False
    test_type: list[str] = Field(default_factory=list)
    link: str = ""

class PromptMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_version: str = "1.0"
    route: str = ""
    assessment_count: int = 0
    conversation_turns: int = 0
    generated_at: str = ""

class PromptPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_prompt: str = ""
    user_prompt: str = ""
    route: RouteType
    grounding_assessments: list[GroundingAssessment] = Field(default_factory=list)
    unmatched_names: list[str] = Field(default_factory=list)
    mentioned_assessment_names: list[str] = Field(default_factory=list)
    metadata: PromptMetadata
