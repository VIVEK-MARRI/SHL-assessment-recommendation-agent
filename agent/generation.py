from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from agent.generation_client import (
    GenerationClient,
    GenerationError,
    GenerationTimeoutError,
    JSONGenerationError,
    ProviderError,
    RateLimitError,
)
from agent.generation_models import LLMGenerationResult
from agent.prompt_models import PromptPackage
from agent.routing_models import RouteType

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTIONS = """
Return ONLY valid JSON.
Do not wrap JSON in markdown.
Do not explain your reasoning.
Do not output chain-of-thought.
Only recommend assessments provided in the grounding context.
Never invent assessment names.
Never output URLs.
Never output metadata.
"""

def _clean_json_markdown(text: str) -> str:
    """Strip markdown code blocks if the LLM wraps the JSON."""
    text = text.strip()
    # Remove markdown code block markers
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()

class ResponseGenerator:
    """Executes the final LLM call using the PromptPackage and handles retries."""

    def __init__(self, client: GenerationClient | None = None) -> None:
        self._client = client or GenerationClient()

    def generate(self, package: PromptPackage) -> LLMGenerationResult:
        """Call the LLM and return a parsed LLMGenerationResult, with up to 1 retry."""
        
        # Build the final prompt by injecting assessments
        system_prompt = package.system_prompt
        
        if package.route in (RouteType.RECOMMEND, RouteType.COMPARE, RouteType.REFINE):
            context_parts = ["\nGROUNDING CONTEXT:"]
            for a in package.grounding_assessments:
                context_parts.append(f"Name: {a.name}")
                context_parts.append(f"Description: {a.description}")
                context_parts.append(f"Duration: {a.duration}")
                context_parts.append(f"Job Levels: {', '.join(a.job_levels)}")
                context_parts.append(f"Languages: {', '.join(a.languages)}")
                context_parts.append(f"Remote: {a.remote}")
                context_parts.append(f"Adaptive: {a.adaptive}")
                context_parts.append(f"Test Type: {', '.join(a.test_type)}")
                context_parts.append(f"Link: {a.link}")
                context_parts.append("---")
            
            if package.grounding_assessments:
                system_prompt += "\n" + "\n".join(context_parts)
            else:
                system_prompt += "\n\nGROUNDING CONTEXT:\nNone available."
                
        # Always append system instructions
        system_prompt += "\n" + SYSTEM_INSTRUCTIONS.strip()
        
        attempt = 1
        max_attempts = 2
        last_error = None
        
        while attempt <= max_attempts:
            try:
                result = self._client.generate(
                    system_prompt=system_prompt,
                    user_payload=package.user_prompt
                )
                
                content = result["content"]
                content = _clean_json_markdown(content)
                
                # Try parsing JSON
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise JSONGenerationError(f"LLM returned invalid JSON: {exc}") from exc
                
                # Validate Schema
                # Note: Validation for hallucinated names is NOT done here per instructions.
                # Only structural validation via Pydantic.
                try:
                    validated = LLMGenerationResult(
                        reply=parsed.get("reply", ""),
                        recommended_names=parsed.get("recommended_names", []),
                        end_of_conversation=parsed.get("end_of_conversation", False),
                        provider=result["provider"],
                        model=result["model"],
                        latency_ms=result["latency_ms"],
                        tokens_prompt=result["tokens_prompt"],
                        tokens_completion=result["tokens_completion"],
                        tokens_total=result["tokens_total"],
                        finish_reason=result["finish_reason"],
                    )
                    
                    # Ensure no extra fields returned by LLM that violate schema
                    # Pydantic extra='forbid' checks if we passed **parsed, but we are pulling manually.
                    # Let's strictly check keys from parsed JSON.
                    allowed_keys = {"reply", "recommended_names", "end_of_conversation"}
                    extra_keys = set(parsed.keys()) - allowed_keys
                    if extra_keys:
                        raise JSONGenerationError(f"LLM returned extra fields: {extra_keys}")
                        
                    return validated
                except ValidationError as exc:
                    raise JSONGenerationError(f"LLM JSON violated schema: {exc}") from exc

            except (JSONGenerationError, GenerationTimeoutError, RateLimitError) as exc:
                last_error = exc
                logger.warning("Attempt %d failed: %s", attempt, exc)
                attempt += 1
            except ProviderError as exc:
                # Retry on 503 or generic ProviderError indicating connection drop/HTTP 500+
                if "503" in str(exc) or "failed" in str(exc).lower():
                    last_error = exc
                    logger.warning("Attempt %d failed (provider/connection): %s", attempt, exc)
                    attempt += 1
                else:
                    raise
            except GenerationError:
                raise
                
        # If we exhausted attempts
        raise last_error or GenerationError("Failed to generate response after retries.")
