"""Deterministic catalog matcher for the Comparison Pipeline.

Matching strategy (in priority order):
  1. Case-insensitive exact match
  2. Normalised exact match (NFKC unicode, collapsed whitespace)
  3. RapidFuzz WRatio ≥ 90  (fallback only)
  4. Reject — never guess below threshold

No embeddings, no BM25, no LLM.
"""

from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path

from rapidfuzz import process as rf_process
from rapidfuzz import fuzz

from agent.comparison_models import ComparisonAssessment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CatalogLoadError(Exception):
    """Raised when catalog.json cannot be loaded."""

class CatalogMatchError(Exception):
    """Raised when catalog matching encounters an unrecoverable error."""


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

_CATALOG_PATH = Path("catalog/catalog.json")
_FUZZY_THRESHOLD = 90


def _normalise(text: str) -> str:
    """Apply NFKC unicode normalisation + lowercase + collapsed whitespace."""
    nfkc = unicodedata.normalize("NFKC", text)
    return " ".join(nfkc.casefold().split())


# ---------------------------------------------------------------------------
# Catalog record → ComparisonAssessment
# ---------------------------------------------------------------------------

def _record_to_assessment(record: dict) -> ComparisonAssessment:  # type: ignore[type-arg]
    return ComparisonAssessment(
        entity_id=str(record.get("entity_id", "")),
        name=record.get("name", ""),
        url=record.get("link", ""),
        test_type=record.get("keys", []),
        description=record.get("description", ""),
        job_levels=record.get("job_levels", []),
        languages=record.get("languages", []),
        duration=record.get("duration", ""),
        remote=bool(record.get("remote", True)),
        adaptive=bool(record.get("adaptive", False)),
        keys=record.get("keys", []),
    )


# ---------------------------------------------------------------------------
# CatalogMatcher
# ---------------------------------------------------------------------------

class CatalogMatcher:
    """Loads catalog.json once and resolves assessment names to catalog records.

    Thread-safety note: loading is idempotent; the catalog is read-only after
    load so concurrent reads are safe without locking.
    """

    def __init__(self, catalog_path: Path | str = _CATALOG_PATH) -> None:
        self._catalog_path = Path(catalog_path)
        self._records: list[dict] = []  # type: ignore[type-arg]
        self._loaded = False
        # Pre-computed index structures populated after load
        self._exact_index: dict[str, dict] = {}   # casefold name → record
        self._norm_index:  dict[str, dict] = {}   # normalised name → record
        self._names: list[str] = []               # original names for fuzzy

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load and index catalog.json.  Idempotent — safe to call multiple times."""
        if self._loaded:
            return
        if not self._catalog_path.exists():
            raise CatalogLoadError(
                f"Catalog not found at {self._catalog_path}. "
                "Run the catalog generation pipeline first."
            )
        try:
            with self._catalog_path.open(encoding="utf-8") as fh:
                self._records = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            raise CatalogLoadError(f"Failed to load catalog: {exc}") from exc

        # Build lookup indices
        for rec in self._records:
            name: str = rec.get("name", "")
            self._exact_index[name.casefold()] = rec
            self._norm_index[_normalise(name)] = rec
            self._names.append(name)

        self._loaded = True
        logger.info(
            "Catalog loaded: path=%s assessments=%d",
            self._catalog_path,
            len(self._records),
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(self, query: str) -> ComparisonAssessment | None:
        """Resolve a single assessment name to a catalog record.

        Returns None if no match meets the threshold — never guesses.
        """
        self._ensure_loaded()

        # Step 1: case-insensitive exact match
        exact = self._exact_index.get(query.casefold())
        if exact is not None:
            logger.info("Exact match: %r → %r", query, exact["name"])
            return _record_to_assessment(exact)

        # Step 2: normalised exact match (NFKC + collapsed whitespace)
        norm_key = _normalise(query)
        norm = self._norm_index.get(norm_key)
        if norm is not None:
            logger.info("Normalised exact match: %r → %r", query, norm["name"])
            return _record_to_assessment(norm)

        # Step 3: RapidFuzz WRatio fallback
        result = rf_process.extractOne(
            query,
            self._names,
            scorer=fuzz.WRatio,
            score_cutoff=_FUZZY_THRESHOLD,
        )
        if result is not None:
            matched_name, score, _ = result
            logger.info(
                "RapidFuzz match: %r → %r  score=%.1f",
                query, matched_name, score,
            )
            record = self._exact_index[matched_name.casefold()]
            return _record_to_assessment(record)

        # Step 4: reject
        logger.info("No match found for: %r", query)
        return None

    def match_many(self, names: list[str]) -> tuple[list[ComparisonAssessment], list[str]]:
        """Resolve a list of assessment names, preserving user order.

        Returns:
            matched:   list of ComparisonAssessment in the same order as *names*
            unmatched: list of original query strings that could not be resolved
        """
        self._ensure_loaded()
        matched: list[ComparisonAssessment] = []
        unmatched: list[str] = []
        for name in names:
            assessment = self.match(name)
            if assessment is not None:
                matched.append(assessment)
            else:
                unmatched.append(name)
                logger.info("Unmatched assessment: %r", name)
        return matched, unmatched

    @property
    def catalog_size(self) -> int:
        self._ensure_loaded()
        return len(self._records)
