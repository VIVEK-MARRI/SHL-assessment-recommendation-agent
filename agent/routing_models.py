from enum import Enum
from typing import Literal
from pydantic import BaseModel

class RouteType(str, Enum):
    REFUSE = "REFUSE"
    CLARIFY = "CLARIFY"
    COMPARE = "COMPARE"
    RECOMMEND = "RECOMMEND"
    REFINE = "REFINE"

class RoutingDecision(BaseModel):
    route: RouteType
    next_module: Literal["query_builder", "comparison_pipeline", "clarification", "refusal"]
    reason: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    clarification_field: str | None = None
    query_required: bool = False
    comparison_required: bool = False
    recommendation_required: bool = False
