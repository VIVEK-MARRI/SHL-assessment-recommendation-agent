import json
import pytest
from pathlib import Path

from agent.response_catalog import ResponseCatalog, CatalogLoadError, CatalogLookupError


@pytest.fixture
def mock_catalog_path(tmp_path: Path) -> Path:
    catalog_path = tmp_path / "catalog.json"
    data = [
        {
            "name": "Python Advanced",
            "link": "http://shl.com/python-adv",
            "keys": ["Knowledge & Skills"],
        },
        {
            "name": "Java Basics",
            "link": "http://shl.com/java-basics",
            "keys": ["Ability & Aptitude"],
        },
        {
            "name": "OPQ32r",
            "link": "http://shl.com/opq32r",
            "keys": ["Personality & Behavior"],
        },
        {"name": " "},  # empty name — should be skipped
        {},  # no name — should be skipped
    ]
    with catalog_path.open("w") as f:
        json.dump(data, f)
    return catalog_path


def test_catalog_load_and_lookup(mock_catalog_path: Path) -> None:
    catalog = ResponseCatalog(catalog_path=mock_catalog_path)
    rec = catalog.lookup("Python Advanced")
    assert rec["name"] == "Python Advanced"
    assert rec["url"] == "http://shl.com/python-adv/"  # catalog normalises to trailing slash
    assert rec["test_type"] == "K"


def test_catalog_lookup_case_insensitive(mock_catalog_path: Path) -> None:
    catalog = ResponseCatalog(catalog_path=mock_catalog_path)
    rec = catalog.lookup("python advanced")
    assert rec["name"] == "Python Advanced"


def test_catalog_lookup_missing(mock_catalog_path: Path) -> None:
    catalog = ResponseCatalog(catalog_path=mock_catalog_path)
    with pytest.raises(CatalogLookupError):
        catalog.lookup("Nonexistent Assessment")


def test_catalog_caching(mock_catalog_path: Path) -> None:
    catalog = ResponseCatalog(catalog_path=mock_catalog_path)
    # Access twice — should use cache (no reload)
    rec1 = catalog.lookup("Java Basics")
    rec2 = catalog.lookup("Java Basics")
    assert rec1 == rec2


def test_catalog_load_error(tmp_path: Path) -> None:
    with pytest.raises(CatalogLoadError):
        ResponseCatalog(catalog_path=tmp_path / "missing.json")


def test_catalog_invalid_format(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text('{"not": "a list"}')
    with pytest.raises(CatalogLoadError):
        ResponseCatalog(catalog_path=path)
