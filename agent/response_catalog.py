from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# test_type code mapping (Issue 1)
# ---------------------------------------------------------------------------

KEY_TO_CODE: dict[str, str] = {
    "Knowledge & Skills": "K",
    "Personality & Behavior": "P",
    "Ability & Aptitude": "A",
    "Biodata & Situational Judgment": "B",
    "Simulations": "S",
    "Competencies": "C",
    "Development & 360": "D",
    "Assessment Exercises": "E",
}


def keys_to_test_type(keys: list[str]) -> str:
    """Convert a list of category keys to a compact comma-joined code string.

    Example: ["Knowledge & Skills", "Simulations"] → "K,S"
    Only known keys are included; unknown keys are silently dropped.
    Returns "K" as a safe default when no known keys are present.
    """
    seen: list[str] = []
    for k in keys:
        code = KEY_TO_CODE.get(k)
        if code and code not in seen:
            seen.append(code)
    return ",".join(seen) if seen else "K"


class CatalogLoadError(Exception):
    """Raised when catalog/catalog.json cannot be loaded."""


class CatalogLookupError(Exception):
    """Raised when a validated name cannot be found in the catalog."""


class ResponseCatalog:
    """Loads and caches catalog.json. Provides lookup of name → (url, test_type)."""

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        if catalog_path is None:
            base_dir = Path(__file__).parent.parent
            self._catalog_path = base_dir / "catalog" / "catalog.json"
        else:
            self._catalog_path = Path(catalog_path)

        # key: lowercase name → value: dict with name, url, test_type
        self._index: dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            with self._catalog_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise CatalogLoadError(
                f"Failed to load catalog from {self._catalog_path}: {exc}"
            ) from exc

        if not isinstance(data, list):
            raise CatalogLoadError("Catalog JSON must be a list of assessments.")

        count = 0
        for item in data:
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()

            # Issue 6: Ensure URL always ends with a trailing slash.
            # catalog.json links never include it; we normalise here so every
            # lookup returns a URL that satisfies the schema requirement.
            url = item.get("link", "")
            if url and not url.endswith("/"):
                url = url + "/"

            # Issue 1: Convert keys list → compact code string ("K", "K,S", etc.)
            raw_keys = item.get("keys") or []
            if not isinstance(raw_keys, list):
                raw_keys = [str(raw_keys)]
            test_type = keys_to_test_type(raw_keys)

            self._index[name.lower()] = {
                "name": name,
                "url": url,
                "test_type": test_type,
            }
            count += 1

        logger.info("ResponseCatalog loaded: %d items cached.", count)

    def lookup(self, name: str) -> dict:
        """
        Lookup a validated name. Returns dict with name, url, test_type.
        Raises CatalogLookupError if not found.
        """
        record = self._index.get(name.strip().lower())
        if record is None:
            raise CatalogLookupError(
                f"Validated name not found in catalog: {name!r}"
            )
        return record

