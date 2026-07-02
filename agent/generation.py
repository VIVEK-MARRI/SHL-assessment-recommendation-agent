from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from agent.conversation_advisor import (
    CatalogRelationshipResolver,
    ConfirmationDetector,
)
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
Keep recommended_names in the same order as the grounding context.
Your JSON output MUST exactly match this structure:
{
  "reply": "your conversational response",
  "recommended_names": [],
  "end_of_conversation": false
}
Never output extra keys.
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


def _filter_grounded_names(names: object, grounded_names: list[str]) -> list[str]:
    """Keep only context-grounded names and preserve retrieval order."""
    if not isinstance(names, list):
        return []

    requested = {str(name).strip().casefold() for name in names if str(name).strip()}
    if not requested:
        return []

    filtered: list[str] = []
    seen: set[str] = set()
    for grounded_name in grounded_names:
        key = grounded_name.casefold()
        if key in requested and key not in seen:
            filtered.append(grounded_name)
            seen.add(key)
    return filtered


def _extract_last_user_message(user_prompt: str) -> str:
    """Extract the last user message from the formatted conversation."""
    parts = re.split(r"\n(?:User|Assistant):\n", user_prompt)
    # The last part is the most recent message
    last = parts[-1].strip() if parts else ""
    # If it ends with an assistant response, backtrack to user part
    if last.startswith(("User:\n", "Assistant:\n")):
        last = re.sub(r"^(User|Assistant):\n", "", last).strip()
    return last


class ResponseGenerator:
    """Executes the final LLM call using the PromptPackage and handles retries."""

    def __init__(
        self,
        client: GenerationClient | None = None,
    ) -> None:
        self._client = client or GenerationClient()
        self._relationship_resolver = CatalogRelationshipResolver()
        self._confirmation_detector = ConfirmationDetector()

    def generate(self, package: PromptPackage) -> LLMGenerationResult:
        """Call the LLM and return a parsed LLMGenerationResult, with up to 1 retry."""
        
        # Build the final prompt by injecting assessments
        system_prompt = package.system_prompt
        
        if package.route in (RouteType.RECOMMEND, RouteType.COMPARE, RouteType.REFINE):
            context_parts = ["\nGROUNDING CONTEXT:"]
            
            # Inject relationship notes first (before individual assessment listings)
            rel_parts: list[str] = []
            assessment_names = [a.name for a in package.grounding_assessments]
            relationship_notes = self._relationship_resolver.format_relationship_context(
                assessment_names
            )
            if relationship_notes:
                rel_parts.append("\nRELATIONSHIP NOTES:")
                rel_parts.append(relationship_notes)
            
            # Inject unmatched names for COMPARE route (assessments user asked about not in catalog)
            if package.route == RouteType.COMPARE and package.unmatched_names:
                unmatched_parts: list[str] = ["\nNOT IN CATALOG:"]
                for name in package.unmatched_names:
                    unmatched_parts.append(f"- {name}")
                context_parts.append("")
                context_parts.extend(unmatched_parts)
                context_parts.append("")
            
            # Build individual assessment entries
            assessment_entries: list[str] = []
            for a in package.grounding_assessments:
                parts: list[str] = []
                parts.append(f"Name: {a.name}")
                parts.append(f"Description: {a.description}")
                parts.append(f"Duration: {a.duration}")
                parts.append(f"Job Levels: {', '.join(a.job_levels)}")
                parts.append(f"Languages: {', '.join(a.languages)}")
                parts.append(f"Remote: {a.remote}")
                parts.append(f"Adaptive: {a.adaptive}")
                parts.append(f"Test Type: {', '.join(a.test_type)}")
                parts.append(f"Link: {a.link}")
                parts.append("---")
                assessment_entries.append("\n".join(parts))
            
            if rel_parts:
                context_parts.extend(rel_parts)
                context_parts.append("")
            
            context_parts.extend(assessment_entries)
            
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
                    if not isinstance(parsed, dict):
                        raise JSONGenerationError("LLM returned a JSON list instead of a dict")
                except json.JSONDecodeError as exc:
                    raise JSONGenerationError(f"LLM returned invalid JSON: {exc}") from exc
                
                # Validate Schema
                # Note: Validation for hallucinated names is NOT done here per instructions.
                # Only structural validation via Pydantic.
                try:
                    recommended_names = parsed.get("recommended_names", [])
                    if package.route in (RouteType.RECOMMEND, RouteType.COMPARE, RouteType.REFINE):
                        recommended_names = _filter_grounded_names(
                            recommended_names,
                            [assessment.name for assessment in package.grounding_assessments],
                        )

                    validated = LLMGenerationResult(
                        reply=parsed.get("reply", ""),
                        recommended_names=recommended_names,
                        end_of_conversation=parsed.get("end_of_conversation", False),
                        provider=result["provider"],
                        model=result["model"],
                        latency_ms=result["latency_ms"],
                        tokens_prompt=result["tokens_prompt"],
                        tokens_completion=result["tokens_completion"],
                        tokens_total=result["tokens_total"],
                        finish_reason=result["finish_reason"],
                    )
                    
                    # Grounding override: if retrieval returned grounded assessments but LLM
                    # incorrectly says "not enough information", force a grounded response.
                    if (
                        package.route in (RouteType.RECOMMEND, RouteType.REFINE, RouteType.COMPARE)
                        and package.grounding_assessments
                    ):
                        not_enough = "not enough information" in validated.reply.lower()
                        empty_recs = len(validated.recommended_names) == 0
                        if not_enough or empty_recs:
                            grounded_names = [a.name for a in package.grounding_assessments]
                            logger.warning(
                                "Grounding override triggered: LLM said '%s' with %d grounding candidates. "
                                "Forcing grounded response.",
                                validated.reply[:80] if not_enough else "no recommendations",
                                len(grounded_names),
                            )
                            validated = LLMGenerationResult(
                                reply="Based on the SHL catalog, here are the most relevant assessments for your requirements.",
                                recommended_names=grounded_names,
                                end_of_conversation=validated.end_of_conversation,
                                provider=validated.provider,
                                model=validated.model,
                                latency_ms=validated.latency_ms,
                                tokens_prompt=validated.tokens_prompt,
                                tokens_completion=validated.tokens_completion,
                                tokens_total=validated.tokens_total,
                                finish_reason=validated.finish_reason,
                            )

                    # Post-processing: detect confirmation from last user message
                    if package.route == RouteType.RECOMMEND:
                        last_user_msg = _extract_last_user_message(package.user_prompt)
                        if self._confirmation_detector.is_confirmation(last_user_msg):
                            logger.info(
                                "Confirmation detected in user message (%.60s), setting end_of_conversation",
                                last_user_msg,
                            )
                            validated = LLMGenerationResult(
                                reply=validated.reply,
                                recommended_names=validated.recommended_names,
                                end_of_conversation=True,
                                provider=validated.provider,
                                model=validated.model,
                                latency_ms=validated.latency_ms,
                                tokens_prompt=validated.tokens_prompt,
                                tokens_completion=validated.tokens_completion,
                                tokens_total=validated.tokens_total,
                                finish_reason=validated.finish_reason,
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
        if package.route == RouteType.REFUSE:
            logger.warning("Generation exhausted attempts for REFUSE route. Returning fallback.")
            return LLMGenerationResult(
                reply="I am sorry, but I can only assist with SHL Assessment Recommendations.",
                recommended_names=[],
                end_of_conversation=False,
                provider=package.metadata.route,
                model="fallback",
                latency_ms=0.0,
                tokens_prompt=0,
                tokens_completion=0,
                tokens_total=0,
                finish_reason="fallback"
            )
        elif package.route == RouteType.CLARIFY:
            logger.warning("Generation exhausted attempts for CLARIFY route. Returning fallback.")
            return LLMGenerationResult(
                reply="Could you please provide more details about the assessment you are looking for?",
                recommended_names=[],
                end_of_conversation=False,
                provider=package.metadata.route,
                model="fallback",
                latency_ms=0.0,
                tokens_prompt=0,
                tokens_completion=0,
                tokens_total=0,
                finish_reason="fallback"
            )

        raise last_error or GenerationError("Failed to generate response after retries.")
