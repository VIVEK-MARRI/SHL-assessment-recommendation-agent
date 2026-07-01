import json
import pytest
from pathlib import Path

from agent.catalog_validator import CatalogValidator, CatalogLoadError

@pytest.fixture
def mock_catalog(tmp_path: Path) -> Path:
    catalog_path = tmp_path / "catalog.json"
    data = [
        {"name": "Python Advanced"},
        {"name": "Java Basics"},
        {"name": "OPQ32r"},
        {"name": " "}, # Empty string should be ignored
        {}, # Missing name
    ]
    with catalog_path.open("w") as f:
        json.dump(data, f)
    return catalog_path

def test_catalog_load(mock_catalog: Path) -> None:
    validator = CatalogValidator(catalog_path=mock_catalog)
    assert validator.validate_name("Python Advanced")
    assert validator.validate_name("OPQ32r")

def test_catalog_case_insensitive(mock_catalog: Path) -> None:
    validator = CatalogValidator(catalog_path=mock_catalog)
    assert validator.validate_name("python advanced")
    assert validator.validate_name("PYTHON ADVANCED")
    assert validator.validate_name("opq32R")

def test_canonicalize_name(mock_catalog: Path) -> None:
    validator = CatalogValidator(catalog_path=mock_catalog)
    assert validator.canonicalize_name("python advanced") == "Python Advanced"
    assert validator.canonicalize_name("opq32R") == "OPQ32r"
    assert validator.canonicalize_name("missing") is None

def test_validate_names(mock_catalog: Path) -> None:
    validator = CatalogValidator(catalog_path=mock_catalog)
    names = [
        "python advanced", # valid
        "C++ Basics",      # invalid
        "PYTHON advanced", # valid duplicate
        "OPQ32r",          # valid
    ]
    valid, invalid = validator.validate_names(names)
    
    # Check deduplication and ordering
    assert valid == ["Python Advanced", "OPQ32r"]
    assert invalid == ["C++ Basics"]

def test_load_error(tmp_path: Path) -> None:
    with pytest.raises(CatalogLoadError):
        CatalogValidator(catalog_path=tmp_path / "missing.json")

def test_invalid_json_format(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    with catalog_path.open("w") as f:
        json.dump({"not_a_list": True}, f)
        
    with pytest.raises(CatalogLoadError):
        CatalogValidator(catalog_path=catalog_path)
