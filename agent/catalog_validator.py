from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CatalogLoadError(Exception):
    """Raised when the catalog cannot be loaded."""


class CatalogValidator:
    """Case-insensitive exact match catalog validator."""

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        if catalog_path is None:
            # Default to catalog/catalog.json
            base_dir = Path(__file__).parent.parent
            self._catalog_path = base_dir / "catalog" / "catalog.json"
        else:
            self._catalog_path = Path(catalog_path)
            
        self._canonical_names: dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load and cache the catalog JSON."""
        try:
            with self._catalog_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise CatalogLoadError(f"Failed to load catalog from {self._catalog_path}: {exc}") from exc
            
        if not isinstance(data, list):
            raise CatalogLoadError("Catalog JSON must be a list of assessments.")
            
        count = 0
        for item in data:
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            self._canonical_names[name.lower()] = name
            count += 1
            
        logger.info("Catalog loaded: %d items cached.", count)

    def validate_name(self, name: str) -> bool:
        """Check if a name exists in the catalog (case-insensitive exact match)."""
        if not isinstance(name, str):
            return False
        return name.strip().lower() in self._canonical_names

    def canonicalize_name(self, name: str) -> str | None:
        """Return the canonical capitalization of a name, or None if not found."""
        if not isinstance(name, str):
            return None
        return self._canonical_names.get(name.strip().lower())

    def validate_names(self, names: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate a list of names. Deduplicates while preserving order.
        Returns:
            (valid_names, invalid_names)
        """
        valid = []
        invalid = []
        seen = set()
        
        for n in names:
            if not isinstance(n, str):
                continue
            
            clean = n.strip()
            clean_lower = clean.lower()
            
            # Deduplicate
            if clean_lower in seen:
                continue
            seen.add(clean_lower)
            
            canonical = self._canonical_names.get(clean_lower)
            if canonical:
                valid.append(canonical)
            else:
                invalid.append(clean)
                
        return valid, invalid
