from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
            url = item.get("link", "")
            test_type = item.get("keys") or []
            if not isinstance(test_type, list):
                test_type = [str(test_type)]

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
