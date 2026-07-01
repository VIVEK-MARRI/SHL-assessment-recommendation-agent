"""Unit tests for deterministic catalog export behavior."""

from __future__ import annotations

import json
from pathlib import Path

from catalog.exporter import export_catalog
from catalog.models import Assessment


def _assessment(entity_id: str, name: str) -> Assessment:
    return Assessment.model_validate(
        {
            "entity_id": entity_id,
            "name": name,
            "link": f"https://www.shl.com/{entity_id.lower()}",
            "description": "Valid description",
            "keys": ["Knowledge & Skills"],
            "job_levels": ["Entry Level"],
            "job_levels_raw": "Entry Level",
            "languages": ["English"],
            "languages_raw": "English",
            "duration": "30 minutes",
            "duration_raw": "30 minutes",
            "status": "active",
            "remote": True,
            "adaptive": False,
        }
    )


def test_export_catalog_stable_ordering(tmp_path: Path) -> None:
    """Exporter should produce deterministic ordering by name and id."""
    destination = tmp_path / "catalog.json"
    records = [_assessment("SHL-2", "B"), _assessment("SHL-1", "A")]

    export_catalog(records, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload[0]["entity_id"] == "SHL-1"
    assert payload[1]["entity_id"] == "SHL-2"


def test_export_catalog_utf8_pretty(tmp_path: Path) -> None:
    """Exporter should write UTF-8 formatted JSON with trailing newline."""
    destination = tmp_path / "catalog.json"
    export_catalog([_assessment("SHL-1", "A")], destination)

    content = destination.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert "\n  {\n" in content
