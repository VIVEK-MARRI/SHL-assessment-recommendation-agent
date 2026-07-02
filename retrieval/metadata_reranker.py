"""Deterministic metadata-aware post-retrieval ranking."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from time import perf_counter

from agent.conversation_models import ConversationState
from agent.query_models import QueryFilters
from retrieval.retrieval_models import RetrievedAssessment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamic technology vocabulary — built from the catalog at import time
# ---------------------------------------------------------------------------

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalog" / "catalog.json"

# Stopwords to exclude from technology-name extraction
_TECH_STOPWORDS: set[str] = {
    "a", "an", "the", "and", "or", "for", "in", "of", "to", "with",
    "new", "old", "basic", "advanced", "general", "expert",
    "development", "programming", "assessment", "knowledge", "skills",
    "test", "tests", "testing", "level", "entry", "professional",
    "individual", "contributor", "manager", "director", "executive",
    "graduate", "intern", "junior", "senior", "lead", "principal",
    "staff", "focus", "solution", "solutions", "end", "user",
    "cloud", "online", "interactive", "verify", "shl", "ms",
    "365", "universal", "competency", "report", "questionnaire",
    "personality", "behavior", "behaviour", "style", "styles",
    "simulation", "simulations", "coding", "interview", "phone",
    "spoken", "sales", "transformation", "global", "skills",
    "measure", "measures", "ability", "aptitude", "reasoning",
    "numerical", "verbal", "inductive", "deductive", "cognitive",
    "situational", "judgment", "judgement", "scenarios", "biodata",
    "competencies", "workplace", "occupational", "dependability",
    "safety", "health", "instrument", "manufacturing", "industrial",
    "retail", "contact", "center", "centre", "service", "services",
    "customer", "admin", "administration", "administrator",
    "financial", "accounting", "statistics", "medical", "terminology",
    "linux", "windows", "word", "excel", "powerpoint", "outlook",
    "microsoft", "office", "team", "leadership", "management",
    "agile", "scrum", "project", "product", "program",
    "operations", "quality", "assurance", "security", "network",
    "networking", "implementation", "support", "technical",
    "professional", "social", "media", "digital", "marketing",
    "business", "analyst", "analysis", "consultant", "specialist",
    "engineer", "developer", "architect", "scientist", "officer",
    "head", "vice", "president", "director", "supervisor",
    "associate", "representative", "manager", "executive",
    "system", "systems", "platform", "infrastructure",
    "automation", "monitoring", "observability", "reliability",
    "continuous", "integration", "delivery", "deployment",
    "operations", "site", "reliability", "devops", "mlops",
    "data", "database", "warehouse", "pipeline", "analytics",
    "intelligence", "learning", "deep", "artificial", "machine",
    "generative", "natural", "language", "processing",
    "computer", "vision", "robotics", "embedded", "firmware",
    "mobile", "web", "frontend", "backend", "fullstack", "full",
    "stack", "api", "rest", "microservice", "microservices",
    "service", "oriented", "architecture", "design", "patterns",
    "version", "control", "git", "testing", "unit", "integration",
    "performance", "tuning", "optimization", "compliance",
    "governance", "risk", "audit", "control", "internal",
    "financial", "accounting", "tax", "treasury", "payroll",
    "hr", "human", "resources", "talent", "acquisition",
    "recruitment", "sourcing", "onboarding", "retention",
    "employee", "relations", "engagement", "culture",
    "change", "transformation", "innovation", "strategy",
    "planning", "execution", "communication", "collaboration",
    "negotiation", "presentation", "writing", "verbal",
    "interpersonal", "critical", "thinking", "problem", "solving",
    "decision", "making", "creativity", "innovation",
    "adaptability", "resilience", "flexibility", "initiative",
    "accountability", "ownership", "integrity", "ethics",
    "diversity", "inclusion", "belonging", "equity",
    "wellbeing", "wellness", "health", "safety", "security",
    "environmental", "sustainability", "corporate", "social",
    "responsibility", "governance", "compliance", "regulatory",
    "legal", "contract", "procurement", "supply", "chain",
    "logistics", "inventory", "warehouse", "distribution",
    "manufacturing", "production", "quality", "control",
    "maintenance", "repair", "overhaul", "field", "service",
}


def _load_catalog_technologies() -> set[str]:
    """Extract technology-like tokens from the SHL catalog.

    Reads catalog.json and collects single-word tokens from assessment names
    that look like specific technologies, platforms, tools, or frameworks.
    Falls back to a hardcoded minimal set if the catalog cannot be read.
    """
    try:
        with _CATALOG_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        logger.warning("Cannot load catalog for technology extraction; using fallback set.")
        return {
            "python", "java", "c#", "r", "php", "ruby", "cobol",
            "javascript", "typescript", "go", "rust", "sql", "c++", "scala",
            "drupal", "mulesoft", "wordpress", "magento", "sap",
            "salesforce", "aws", "azure", "gcp", "docker", "kubernetes",
            "hadoop", "spark", "kafka", "terraform", "ansible",
            "puppet", "chef", "jenkins", "gitlab", "github",
            "jira", "confluence", "slack", "postman", "swagger",
            "spring", "hibernate", "struts", "servlet", "jsp", "jdbc",
            "angular", "react", "vue", "node", "express", "django",
            "flask", "rails", "laravel", "symfony", "yii", "cakephp",
            "aspnet", "dotnet", "csharp", "fsharp", "vbnet", "vb",
            "swift", "kotlin", "flutter", "reactnative", "xamarin",
            "oracle", "mysql", "postgresql", "mongodb", "sqlite",
            "redis", "cassandra", "mariadb", "dynamodb", "cosmosdb",
            "firebase", "snowflake", "bigquery", "redshift",
        }

    technology_terms: set[str] = set()
    for record in records:
        name: str = record.get("name", "")
        tokens = re.findall(r"[a-zA-Z0-9+#.]+", name)
        for token in tokens:
            cleaned = token.strip().casefold().strip(".")
            if cleaned and cleaned not in _TECH_STOPWORDS and len(cleaned) > 1:
                # Normalize common suffixes
                if cleaned.endswith("(new)"):
                    cleaned = cleaned[:-5].strip()
                if cleaned:
                    technology_terms.add(cleaned)

    # Merge with the hardcoded fallback to ensure coverage
    technology_terms.update({
        "python", "java", "c#", "r", "php", "ruby", "cobol",
        "javascript", "typescript", "go", "rust", "sql", "c++", "scala",
    })

    logger.info("Loaded %d technology terms from catalog.", len(technology_terms))
    return technology_terms


# Build the technology set once at module load time
_DYNAMIC_TECHNOLOGIES: set[str] = _load_catalog_technologies()

WEIGHT_EXACT_NAME_SKILL = 120.0
WEIGHT_NAME_SKILL = 90.0
WEIGHT_KEY_SKILL = 70.0
WEIGHT_DESCRIPTION_SKILL = 25.0
WEIGHT_ROLE = 24.0
WEIGHT_SENIORITY = 22.0
WEIGHT_JOB_LEVEL = 20.0
WEIGHT_TEST_TYPE = 24.0
WEIGHT_DURATION = 18.0
WEIGHT_LANGUAGE = 8.0
WEIGHT_CAPABILITY = 16.0
PENALTY_UNRELATED_TECH = 80.0
PENALTY_DURATION_OVER = 160.0
PENALTY_LANGUAGE_MISMATCH = 50.0
PENALTY_EXCLUDED_CAPABILITY = 140.0

# Legacy constant kept for backward compatibility; _DYNAMIC_TECHNOLOGIES is used at runtime
_KNOWN_TECHNOLOGIES = _DYNAMIC_TECHNOLOGIES

_TEST_TYPE_CODES = {
    "knowledge & skills": {"k", "knowledge", "skills", "knowledge & skills"},
    "personality & behavior": {"p", "personality", "behavior", "competencies"},
    "ability & aptitude": {"a", "ability", "aptitude", "cognitive"},
    "simulations": {"s", "simulation", "simulations"},
}

_CAPABILITY_TERMS = {
    "personality": {"personality", "behavior", "opq", "competencies"},
    "cognitive": {"cognitive", "ability", "aptitude", "reasoning"},
    "simulation": {"simulation", "simulations", "coding simulation"},
    "leadership": {"leadership", "manager", "management"},
}


class MetadataReranker:
    """Post-retrieval re-ranking using attached metadata."""

    @classmethod
    def rerank(
        cls,
        results: list[RetrievedAssessment],
        state: ConversationState,
        filters: QueryFilters,
    ) -> list[RetrievedAssessment]:
        """Apply deterministic metadata boosting and penalties."""
        started_at = perf_counter()

        reranked_results = []
        for original_position, assessment in enumerate(results, start=1):
            original_score = assessment.rrf_score or assessment.score
            skill_boost = cls._calculate_skill_boost(assessment, state.technical_skills)
            role_boost = cls._calculate_role_boost(assessment, state.role)
            job_level_boost = cls._calculate_job_level_boost(assessment, filters)
            seniority_boost = cls._calculate_seniority_boost(assessment, state.seniority, filters)
            type_boost = cls._calculate_type_boost(assessment, filters)
            capability_boost = cls._calculate_capability_boost(assessment, state)
            duration_adjustment = cls._calculate_duration_adjustment(assessment, filters)
            language_adjustment = cls._calculate_language_adjustment(assessment, filters)
            tech_penalty = cls._calculate_technology_penalty(assessment, state.technical_skills, state.role)
            exclusion_penalty = cls._calculate_exclusion_penalty(assessment, state.constraints)

            metadata_score = (
                skill_boost
                + role_boost
                + job_level_boost
                + seniority_boost
                + type_boost
                + capability_boost
                + duration_adjustment
                + language_adjustment
                - tech_penalty
                - exclusion_penalty
            )
            final_score = original_score + metadata_score

            logger.info(
                (
                    "Reranking %s: base=%.4f skill=%.2f role=%.2f jl=%.2f seniority=%.2f "
                    "type=%.2f capability=%.2f duration=%.2f language=%.2f "
                    "tech_penalty=%.2f exclusion_penalty=%.2f -> %.4f"
                ),
                assessment.entity_id,
                original_score,
                skill_boost,
                role_boost,
                job_level_boost,
                seniority_boost,
                type_boost,
                capability_boost,
                duration_adjustment,
                language_adjustment,
                tech_penalty,
                exclusion_penalty,
                final_score,
            )

            reranked_results.append(
                assessment.model_copy(
                    update={
                        "score": final_score,
                    }
                )
            )

        reranked_results.sort(
            key=lambda item: (
                -item.score,
                -(item.rrf_score or 0.0),
                item.embedding_rank or 999_999,
                item.bm25_rank or 999_999,
                item.entity_id,
            )
        )

        # Re-assign ranks
        for i, res in enumerate(reranked_results, start=1):
            res.rank = i

        logger.info(
            "Reranking completed for %d results in %.2fms",
            len(results),
            (perf_counter() - started_at) * 1000,
        )
        return reranked_results

    @classmethod
    def _calculate_duration_adjustment(cls, assessment: RetrievedAssessment, filters: QueryFilters) -> float:
        if filters.maximum_duration_minutes is None or assessment.duration_minutes is None:
            return 0.0
        if assessment.duration_minutes <= filters.maximum_duration_minutes:
            return WEIGHT_DURATION
        return -PENALTY_DURATION_OVER

    @classmethod
    def _calculate_language_adjustment(cls, assessment: RetrievedAssessment, filters: QueryFilters) -> float:
        if not filters.languages or not assessment.languages:
            return 0.0
        requested = {_normalise_text(value) for value in filters.languages}
        available = {_normalise_text(value) for value in assessment.languages}
        if requested.intersection(available):
            return WEIGHT_LANGUAGE
        return -PENALTY_LANGUAGE_MISMATCH

    @classmethod
    def _calculate_skill_boost(cls, assessment: RetrievedAssessment, technical_skills: list[str]) -> float:
        """Boost score if technical skills match name, keys, or description."""
        if not technical_skills:
            return 0.0

        boost = 0.0
        name = _normalise_text(assessment.name)
        keys = [_normalise_text(k) for k in assessment.keys]
        description = _normalise_text(assessment.description)

        for skill in technical_skills:
            skill_text = _normalise_text(skill)
            if not skill_text:
                continue

            if skill_text == name or _contains_phrase(name, skill_text):
                boost += WEIGHT_NAME_SKILL
                if name.startswith(skill_text):
                    boost += WEIGHT_EXACT_NAME_SKILL - WEIGHT_NAME_SKILL
            elif any(_contains_phrase(key, skill_text) for key in keys):
                boost += WEIGHT_KEY_SKILL
            elif _contains_phrase(description, skill_text):
                boost += WEIGHT_DESCRIPTION_SKILL

        return boost

    @classmethod
    def _calculate_role_boost(cls, assessment: RetrievedAssessment, role: str | None) -> float:
        if not role:
            return 0.0
        role_tokens = _tokens(role) - _ROLE_STOPWORDS
        if not role_tokens:
            return 0.0

        haystack = _tokens(" ".join([assessment.name, assessment.description, " ".join(assessment.keys)]))
        matches = role_tokens.intersection(haystack)
        return min(len(matches) * WEIGHT_ROLE, WEIGHT_ROLE * 2)

    @classmethod
    def _calculate_job_level_boost(
        cls,
        assessment: RetrievedAssessment,
        filters: QueryFilters,
    ) -> float:
        """Boost assessments whose job levels match the requested filters."""
        if not filters.job_levels or not assessment.job_levels:
            return 0.0

        requested = {_normalise_text(jl) for jl in filters.job_levels}
        available = {_normalise_text(jl) for jl in assessment.job_levels}
        matching = requested.intersection(available)
        if matching:
            return WEIGHT_JOB_LEVEL * len(matching)
        return 0.0

    @classmethod
    def _calculate_seniority_boost(
        cls,
        assessment: RetrievedAssessment,
        seniority: str | None,
        filters: QueryFilters,
    ) -> float:
        score = 0.0
        if filters.job_levels and assessment.job_levels:
            requested = {_normalise_text(level) for level in filters.job_levels}
            available = {_normalise_text(level) for level in assessment.job_levels}
            if requested.intersection(available):
                score += WEIGHT_SENIORITY

        if seniority:
            seniority_tokens = _tokens(seniority)
            haystack = _tokens(" ".join([assessment.name, assessment.description, " ".join(assessment.job_levels)]))
            if seniority_tokens.intersection(haystack):
                score += WEIGHT_SENIORITY / 2

        return score

    @classmethod
    def _calculate_type_boost(cls, assessment: RetrievedAssessment, filters: QueryFilters) -> float:
        if not filters.test_types:
            return 0.0

        assessment_types = cls._assessment_type_terms(assessment)
        score = 0.0
        for requested_type in filters.test_types:
            expected = _TEST_TYPE_CODES.get(_normalise_text(requested_type), {_normalise_text(requested_type)})
            if assessment_types.intersection(expected):
                score += WEIGHT_TEST_TYPE
        return score

    @classmethod
    def _calculate_capability_boost(cls, assessment: RetrievedAssessment, state: ConversationState) -> float:
        requested: list[str] = []
        if state.personality_required:
            requested.append("personality")
        if state.cognitive_required:
            requested.append("cognitive")
        if state.simulation_required:
            requested.append("simulation")
        if state.leadership_required:
            requested.append("leadership")
        if not requested:
            return 0.0

        haystack = cls._assessment_type_terms(assessment)
        haystack.update(_tokens(" ".join([assessment.name, assessment.description, " ".join(assessment.keys)])))
        score = 0.0
        for capability in requested:
            if haystack.intersection(_CAPABILITY_TERMS[capability]):
                score += WEIGHT_CAPABILITY
        return score

    @classmethod
    def _calculate_technology_penalty(cls, assessment: RetrievedAssessment, technical_skills: list[str], role: str | None = None) -> float:
        """Penalize assessment if it focuses on unrelated known technologies.

        Checks both explicit technical_skills and technologies implied by role
        (e.g. "Python developer" -> "python").
        """
        requested_techs: set[str] = set()
        for skill in technical_skills:
            requested_techs.add(_normalise_text(skill))

        # Extract implied technologies from role (e.g. "Python developer" -> "python")
        if role:
            role_lower = role.casefold()
            for known_tech in _KNOWN_TECHNOLOGIES:
                if known_tech in role_lower:
                    requested_techs.add(known_tech)

        if not requested_techs:
            return 0.0

        focus_text = _normalise_text(" ".join([assessment.name, " ".join(assessment.keys)]))

        for req in requested_techs:
            if _contains_phrase(focus_text, req):
                return 0.0

        for known_tech in _KNOWN_TECHNOLOGIES:
            if known_tech not in requested_techs:
                if _contains_phrase(focus_text, known_tech):
                    return PENALTY_UNRELATED_TECH

        return 0.0

    @classmethod
    def _calculate_exclusion_penalty(cls, assessment: RetrievedAssessment, constraints: list[str]) -> float:
        excluded_capabilities: set[str] = set()
        text = " ".join(constraints).casefold()
        if re.search(r"\b(?:no|without|exclude)\s+personality\b", text):
            excluded_capabilities.add("personality")
        if re.search(r"\b(?:no|without|exclude)\s+simulation", text):
            excluded_capabilities.add("simulation")
        if re.search(r"\b(?:no|without|exclude)\s+opq\b", text):
            excluded_capabilities.add("personality")
        if not excluded_capabilities:
            return 0.0

        haystack = cls._assessment_type_terms(assessment)
        haystack.update(_tokens(" ".join([assessment.name, assessment.description, " ".join(assessment.keys)])))
        penalty = 0.0
        for capability in excluded_capabilities:
            if haystack.intersection(_CAPABILITY_TERMS[capability]):
                penalty += PENALTY_EXCLUDED_CAPABILITY
        return penalty

    @staticmethod
    def _assessment_type_terms(assessment: RetrievedAssessment) -> set[str]:
        terms = set()
        for value in [assessment.test_type, *assessment.keys]:
            terms.update(_tokens(value))
            normalised = _normalise_text(value)
            if normalised:
                terms.add(normalised)
        return terms


_ROLE_STOPWORDS = {
    "assessment",
    "developer",
    "engineer",
    "candidate",
    "hire",
    "hiring",
    "test",
    "tests",
    "role",
    "roles",
    "for",
    "and",
    "or",
    "the",
}


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().replace("(new)", " ")).strip()


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]+", _normalise_text(value)))


def _contains_phrase(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None
