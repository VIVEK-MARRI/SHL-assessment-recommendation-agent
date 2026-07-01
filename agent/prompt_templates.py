from __future__ import annotations

import logging
from pathlib import Path

from agent.routing_models import RouteType

logger = logging.getLogger(__name__)

class TemplateLoadError(Exception):
    """Raised when a prompt template cannot be loaded from disk."""

class PromptTemplates:
    """Loads and caches prompt templates from disk."""

    def __init__(self, templates_dir: Path | str = Path("agent/prompts")) -> None:
        self._dir = Path(templates_dir)
        self._cache: dict[RouteType, str] = {}
        
        self._file_map = {
            RouteType.RECOMMEND: "recommendation_prompt.txt",
            RouteType.COMPARE: "comparison_prompt.txt",
            RouteType.CLARIFY: "clarification_prompt.txt",
            RouteType.REFUSE: "refusal_prompt.txt",
            RouteType.REFINE: "recommendation_prompt.txt", # Refine uses recommendation prompt
        }

    def get_template(self, route: RouteType) -> str:
        if route in self._cache:
            return self._cache[route]
            
        filename = self._file_map.get(route)
        if not filename:
            raise TemplateLoadError(f"No template mapped for route: {route}")
            
        filepath = self._dir / filename
        if not filepath.exists():
            raise TemplateLoadError(f"Template file not found: {filepath}")
            
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                self._cache[route] = content
                logger.info(f"Loaded template for {route.value} from {filepath}")
                return content
        except Exception as e:
            raise TemplateLoadError(f"Failed to read template {filepath}: {e}") from e
