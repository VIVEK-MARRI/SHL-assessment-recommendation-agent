"""Conversational intelligence helpers for deterministic response enhancement.

Provides catalog relationship analysis, confirmation detection,
tradeoff detection, and catalog limitation handling — all without
modifying the locked retrieval/validation/response architecture.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DERIVED_SUFFIXES = frozenset({
    "report", "profile", "narrative", "feedback", "candidate",
})

_CONFIRMATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(looks?\s+good|perfect|great|excellent|beautiful|awesome|fantastic)\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(that'?s\s+what\s+(we|i)\s+need|this\s+is\s+(what\s+)?(we|i)\s+need)\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(let'?s\s+go\s+(with|for)\s*(it|this|that)?|go\s+(with|for)\s+(it|this|that))\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(works?\s+for\s+me|fine\s+by\s+me|i'?ll\s+take\s+(it|these|this|that))\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(yes|yeah|yep|sure|ok(?:ay)?|kk|alright|definitely|absolutely)\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*thanks?\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(that'?s|this\s+is)\s+(great|perfect|excellent|correct|right)\s*[.!]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*make(?:s)?\s+sense\s*[.!]*\s*$", re.IGNORECASE),
]

_TRADEOFF_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdo\s+(i|we)\s+(really\s+)?need\b", re.IGNORECASE),
    re.compile(r"\bis\s+(it|this|that)\s+necessary\b", re.IGNORECASE),
    re.compile(r"\bis\s+it\s+worth\s+(it|doing|having)\b", re.IGNORECASE),
    re.compile(r"\bcan\s+(we|i)\s+(skip|omit|drop|remove)\b", re.IGNORECASE),
    re.compile(r"\bis\s+there\s+(a|an|any)\s+(benefit|value|point)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+do\s+(i|we)\s+(gain|lose)\b", re.IGNORECASE),
    re.compile(r"\bwhat'?s\s+the\s+(point|use|benefit)\b", re.IGNORECASE),
]

_COMPARISON_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\b(compare|difference|diff|vs\.?|versus)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+do\s+.+?\s+(compare|differ)\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(one|is|would|should)\b", re.IGNORECASE),
    re.compile(r"\bwhat'?s\s+the\s+difference\b", re.IGNORECASE),
]

_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


# ---------------------------------------------------------------------------
# CatalogRelationshipResolver
# ---------------------------------------------------------------------------

class CatalogRelationshipResolver:
    """Discovers relationships between catalog items from name patterns.

    Detects two types of relationship:

    1. **Code-based families** — items sharing a product code (OPQ, MFS, Verify, etc.)
       where one is the base assessment and others are derived reports.

    2. **Name-based families** — items sharing the first 2-3 significant words
       where one is the base assessment and others are derived reports.
    """

    # Known product codes that define assessment families
    # (code, display_name) — display_name used for relationship description text
    _PRODUCT_CODES: list[tuple[str, str]] = [
        ("opq", "OPQ"),
        ("verify", "Verify"),
        ("mfs", "MFS"),
        ("dsi", "DSI"),
        ("mq", "MQ"),
        ("pjm", "PJM"),
        ("writex", "WriteX"),
        ("svar", "SVAR"),
        ("ucf", "UCF"),
        ("hiPo", "HiPo"),
    ]

    def __init__(self, catalog_path: Path | None = None) -> None:
        self._catalog_path = catalog_path or _CATALOG_DIR / "catalog.json"
        self._catalog: list[dict[str, Any]] = []
        self._name_index: dict[str, dict[str, Any]] = {}
        self._relationships: dict[str, list[str]] = {}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        try:
            with self._catalog_path.open("r", encoding="utf-8") as f:
                self._catalog = json.load(f)
        except Exception as exc:
            logger.warning("Failed to load catalog for relationship resolver: %s", exc)
            return

        self._name_index = {}
        for item in self._catalog:
            name = item.get("name", "").strip()
            if name:
                self._name_index[name.lower()] = item

        self._build_relationships()
        self._loaded = True
        logger.info("CatalogRelationshipResolver loaded: %d items", len(self._catalog))

    def _is_derived(self, name: str) -> bool:
        lower = name.lower()
        return any(kw in lower for kw in _DERIVED_SUFFIXES)

    def _base_name(self, name: str) -> str:
        cleaned = re.sub(r"\s*\(New\)\s*", "", name, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*\(MFS\)\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*v\d+(\.\d+)?\s*$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _extract_codes(self, name: str) -> set[str]:
        """Extract known product codes from an assessment name.

        Matches product codes as standalone words (e.g. "OPQ") or as
        embedded prefixes (e.g. "OPQ32r" where "OPQ" is followed by a digit).
        """
        lower = name.lower()
        found: set[str] = set()
        for code, _display in self._PRODUCT_CODES:
            # Match as standalone word: "opq" in "OPQ Leadership Report"
            if re.search(rf"(?<!\w){re.escape(code)}(?!\w)", lower):
                found.add(code)
            # Match as embedded prefix before a digit: "opq" in "OPQ32r"
            elif re.search(rf"(?<!\w){re.escape(code)}\d", lower):
                found.add(code)
        return found

    def _build_relationships(self) -> None:
        """Build family relationships: base assessments → derived reports."""
        families: dict[str, list[dict[str, Any]]] = {}

        for item in self._catalog:
            name = item.get("name", "")
            base = self._base_name(name)
            codes = self._extract_codes(base)

            for code in codes:
                if code not in families:
                    families[code] = []
                families[code].append(item)

            words = [w for w in base.split() if w.lower() not in {
                "the", "a", "an", "of", "in", "for", "and", "or", "to",
            }]
            if len(words) < 2:
                continue
            for n_words in range(min(3, len(words)), 1, -1):
                key = " ".join(words[:n_words]).lower()
                if key not in families:
                    families[key] = []
                families[key].append(item)
                break

        # For each family, separate base assessments from derived reports
        for key, members in families.items():
            bases = [m for m in members if not self._is_derived(m.get("name", ""))]
            derived = [m for m in members if self._is_derived(m.get("name", ""))]
            if bases and derived:
                for base_item in bases:
                    base_name = base_item["name"]
                    derived_names = [d["name"] for d in derived]
                    if base_name.lower() not in self._relationships:
                        self._relationships[base_name.lower()] = []
                    for dn in derived_names:
                        if dn not in self._relationships[base_name.lower()]:
                            self._relationships[base_name.lower()].append(dn)

    def get_relationships(self, name: str) -> list[str]:
        """Get derived reports/assessments related to a base assessment."""
        self.load()
        return self._relationships.get(name.lower(), [])

    def get_family(self, name: str) -> list[str]:
        """Get all items in the same family (base + derived)."""
        self.load()
        name_lower = name.lower()

        # Check if this is a base with relationships or a derived item
        if name_lower in self._relationships:
            rels = self._relationships[name_lower]
            return [name] + [r for r in rels if r.lower() != name_lower]

        # Check if this is a derived item that belongs to a base
        for base_name, derived_names in self._relationships.items():
            if any(name_lower == d.lower() for d in derived_names):
                return [self._name_index.get(base_name, {}).get("name", base_name)] + derived_names

        return [name]

    def is_base_assessment(self, name: str) -> bool:
        """Check if this is likely a base assessment (not a derived report)."""
        return not self._is_derived(name)

    def format_relationship_context(self, names: list[str]) -> str:
        """Build a human-readable relationship note for a list of assessments."""
        self.load()
        parts: list[str] = []
        seen_bases: set[str] = set()

        for n in names:
            rels = self.get_relationships(n)
            if rels and n not in seen_bases:
                parts.append(f"{n} is the base assessment. Related reports: {', '.join(rels[:3])}.")
                seen_bases.add(n)

        # Also check if any of the names are derived from the same base
        for n in names:
            for base_name, rels in self._relationships.items():
                if any(n.lower() == d.lower() for d in rels):
                    base_display = self._name_index.get(base_name, {}).get("name", base_name)
                    if base_display not in seen_bases:
                        parenthetical = f" ({', '.join(rels[:3])})" if rels else ""
                        parts.append(f"{n} is a report derived from {base_display}{parenthetical}.")
                        seen_bases.add(base_display)

        return "\n".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# ConfirmationDetector
# ---------------------------------------------------------------------------

class ConfirmationDetector:
    """Deterministically detects when a user confirms, approves, or ends."""

    def is_confirmation(self, text: str) -> bool:
        """Check if the user is confirming/approving the recommendation."""
        return any(p.search(text.strip()) for p in _CONFIRMATION_PATTERNS)

    def is_tradeoff_question(self, text: str) -> bool:
        """Check if user is asking about necessity or value of an assessment."""
        return any(p.search(text) for p in _TRADEOFF_PATTERNS)

    def is_comparison_request(self, text: str) -> bool:
        """Check if user is asking for a comparison."""
        return any(p.search(text) for p in _COMPARISON_TRIGGERS)


# ---------------------------------------------------------------------------
# CatalogLimitationHandler
# ---------------------------------------------------------------------------

class CatalogLimitationHandler:
    """Handles cases where no exact match exists in the catalog."""

    def __init__(self, resolver: CatalogRelationshipResolver | None = None) -> None:
        self._resolver = resolver or CatalogRelationshipResolver()

    def find_nearest_alternatives(self, query: str) -> list[str]:
        """Find nearest grounded alternatives for a query not in catalog."""
        self._resolver.load()
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())

        scored: list[tuple[int, str]] = []
        for name_lower, record in self._resolver._name_index.items():
            name_words = set(name_lower.split())
            overlap = len(query_words & name_words)
            if overlap >= 1:
                scored.append((overlap, record.get("name", "")))

        scored.sort(key=lambda x: (-x[0], x[1]))
        return [name for _, name in scored[:5]]

    def is_in_catalog(self, query: str) -> bool:
        """Check if a query matches any catalog item."""
        self._resolver.load()
        query_lower = query.lower().strip()
        return query_lower in self._resolver._name_index

    def find_unsupported_technologies(
        self, user_message: str, catalog_names: list[str]
    ) -> list[str]:
        """Find technologies/skills mentioned in user message with no dedicated catalog assessment.

        Checks each word/phrase in the user message against catalog item names.
        Returns technologies that appear to be specific skill requests without
        a matching dedicated assessment.
        """
        self._resolver.load()
        catalog_lower = {n.lower() for n in catalog_names}
        # Also include individual significant words from catalog names
        catalog_words: set[str] = set()
        for name in catalog_lower:
            for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]+", name):
                if len(word) > 2:
                    catalog_words.add(word.lower())

        # Extract potential technology mentions from user message
        # Look for patterns like "I need X", "assessments for X", "X assessment"
        message_lower = user_message.lower()
        
        # First check: extract noun phrases that might be technology names
        # Simple heuristic: look for words after "need", "for", "in" that aren't stopwords
        stopwords = {
            "the", "a", "an", "this", "that", "these", "those", "it", "its",
            "some", "any", "all", "each", "every", "both", "few", "several",
            "assessments", "assessment", "test", "tests", "hiring", "hire",
            "looking", "need", "needs", "wanted", "like", "would", "could",
            "please", "help", "me", "us", "our", "we", "i", "you", "your",
            "about", "with", "from", "have", "has", "had", "get", "got",
            "know", "knows", "known", "using", "use", "used", "does", "do",
        }
        
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]+", message_lower)
        potential_techs: list[str] = []
        for word in words:
            w = word.lower().strip(".")
            if w not in stopwords and len(w) >= 2:
                potential_techs.append(w)

        # Check each potential technology against catalog
        unsupported: list[str] = []
        for tech in potential_techs:
            # If it directly matches a catalog name, it has a dedicated assessment
            if tech in catalog_lower:
                continue
            # If it appears as a significant word in any catalog name, it might be supported
            tech_stem = tech.lower().strip("s")  # Simple plural handling
            if tech_stem in catalog_words or tech in catalog_words:
                continue
            unsupported.append(tech)

        # Deduplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for tech in unsupported:
            t = tech.lower()
            if t not in seen:
                seen.add(t)
                result.append(tech)
        return result


# ---------------------------------------------------------------------------
# ClarificationAnalyzer
# ---------------------------------------------------------------------------

_CLARIFICATION_QUESTIONS: dict[str, str] = {
    "role": "What role or position are you hiring for?",
    "seniority": "What seniority level is this for — entry level, mid-level, senior, or executive?",
    "purpose": "Is this for hiring or development?",
    "technical_skills": "What specific technical skills or tools do you need to assess?",
    "constraints": "Do you have any constraints like language, duration, or remote testing requirements?",
}

class ClarificationAnalyzer:
    """Determines the single highest-value missing piece of information."""

    def determine_missing_field(self, state: Any) -> str | None:
        """Return the single most valuable missing information field."""
        if not state.role:
            return "role"
        if not state.seniority:
            return "seniority"
        if not state.technical_skills:
            return "technical_skills"
        if not state.constraints:
            return "constraints"
        return None

    def get_clarification_question(self, field: str) -> str:
        """Get a natural clarification question for a missing field."""
        return _CLARIFICATION_QUESTIONS.get(
            field,
            "Could you provide more details about your requirements?",
        )


# ---------------------------------------------------------------------------
# LegalDisclaimerHandler
# ---------------------------------------------------------------------------

_LEGAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(eeoc|ada|adverse impact|disparate impact|title vii)\b", re.IGNORECASE),
    re.compile(r"\b(legal|regulation|regulatory|compliance|compliant|comply|complies)\b", re.IGNORECASE),
    re.compile(r"\b(regulations?\s+on|regulations?\s+for|required\s+by\s+law)\b", re.IGNORECASE),
    re.compile(r"\b(is\s+it\s+legal|are\s+they\s+legal|legally\s+required)\b", re.IGNORECASE),
    re.compile(r"\b(satisf(?:y|ies|ied)\s+(legal|regulatory|regulations?|compliance))\b", re.IGNORECASE),
    re.compile(r"\b(govern(?:s|ing|ment|ance)\s+(regulation|compliance|mandate))\b", re.IGNORECASE),
]

LEGAL_DISCLAIMER: str = (
    "I can explain what the assessment measures, but I can't determine "
    "whether it satisfies legal or regulatory requirements."
)

class LegalDisclaimerHandler:
    """Handles legal/compliance questions about SHL assessments."""

    def is_legal_compliance_question(self, text: str) -> bool:
        """Check if the user is asking about legal/regulatory compliance."""
        return any(p.search(text) for p in _LEGAL_PATTERNS)

    def format_disclaimer_response(self, original_reply: str = "") -> str:
        """Return a response that includes the legal disclaimer."""
        if original_reply and LEGAL_DISCLAIMER not in original_reply:
            return f"{LEGAL_DISCLAIMER}\n\n{original_reply}"
        return original_reply or LEGAL_DISCLAIMER
