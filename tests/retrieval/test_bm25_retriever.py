"""Unit tests for retrieval.bm25_retriever."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi
import pytest

from retrieval.bm25_index import build_bm25_config, persist_bm25_index
from retrieval.bm25_models import BM25DocumentRecord
from retrieval.bm25_retriever import BM25Retriever, BM25RetrieverError


def _records() -> list[BM25DocumentRecord]:
    return [
        BM25DocumentRecord(
            offset=0,
            entity_id="cpp",
            document="Name:\nC++ Developer\n\nCategories:\nKnowledge & Skills (K)",
            tokens=["cpp", "developer"],
            name="C++ Developer",
            url="https://www.shl.com/cpp",
            test_type="K",
            keys=["Knowledge & Skills"],
        ),
        BM25DocumentRecord(
            offset=1,
            entity_id="sales",
            document="Name:\nSales Manager\n\nCategories:\nPersonality & Behavior (P)",
            tokens=["sales", "manager"],
            name="Sales Manager",
            url="https://www.shl.com/sales",
            test_type="P",
            keys=["Personality & Behavior"],
        ),
        BM25DocumentRecord(
            offset=2,
            entity_id="python",
            document="Name:\nPython Developer\n\nCategories:\nKnowledge & Skills (K)",
            tokens=["python", "developer"],
            name="Python Developer",
            url="https://www.shl.com/python",
            test_type="K",
            keys=["Knowledge & Skills"],
        ),
    ]


def _write_bm25(tmp_path: Path) -> tuple[Path, Path, Path]:
    records = _records()
    index = BM25Okapi([record.tokens for record in records])
    config = build_bm25_config("sha256", len(records), 2.0, 5)
    index_path = tmp_path / "bm25_index.pkl"
    corpus_path = tmp_path / "bm25_corpus.json"
    config_path = tmp_path / "bm25_config.json"
    persist_bm25_index(index, records, config, index_path, corpus_path, config_path)
    return index_path, corpus_path, config_path


def _retriever(tmp_path: Path) -> BM25Retriever:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    return BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)


def test_initialization_loads_index_and_corpus(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()

    health = retriever.health()
    assert health.bm25_loaded is True
    assert health.corpus_loaded is True
    assert health.document_count == 3
    assert health.tokenizer_version == "1.0"
    assert health.catalog_sha256 == "sha256"
    assert health.average_query_latency_ms is None


def test_singleton_loading_reused_across_searches(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    loader_calls = 0

    def loader(*args, **kwargs):
        nonlocal loader_calls
        loader_calls += 1
        from retrieval.bm25_loader import load_bm25_index

        return load_bm25_index(*args, **kwargs)

    retriever = BM25Retriever(
        index_path,
        corpus_path,
        config_path,
        catalog_path=None,
        loader=loader,
    )
    retriever.initialize()
    retriever.search("developer")
    retriever.search("developer")

    assert loader_calls == 1


def test_valid_query_returns_results(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("python developer", top_k=2)

    assert results[0].retrieval_source == "bm25"
    assert results[0].bm25_rank == 1
    assert results[0].embedding_rank is None
    assert retriever.health().average_query_latency_ms is not None


def test_empty_query_raises(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()

    with pytest.raises(BM25RetrieverError, match="empty"):
        retriever.search("   \n\t  ")


def test_unicode_technical_query_is_tokenized(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("Ｃ＋＋ developer", top_k=1)

    assert results[0].entity_id == "cpp"


def test_threshold_filtering(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("python", top_k=3, minimum_score=0.1)

    assert [result.entity_id for result in results] == ["python"]


def test_ranking_order(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    results = retriever.search("developer", top_k=3)

    assert [result.score for result in results] == sorted(
        [result.score for result in results],
        reverse=True,
    )


def test_metadata_resolution(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    result = retriever.search("sales manager", top_k=1)[0]

    assert result.name == "Sales Manager"
    assert result.url == "https://www.shl.com/sales"
    assert result.keys == ["Personality & Behavior"]


def test_missing_artifacts_raise(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    index_path.unlink()
    retriever = BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)

    with pytest.raises(BM25RetrieverError, match="not found"):
        retriever.initialize()


def test_corrupted_pickle_raises(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    index_path.write_bytes(b"not pickle")
    retriever = BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)

    with pytest.raises(BM25RetrieverError):
        retriever.initialize()


def test_tokenizer_mismatch_raises(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["tokenizer_version"] = "0.0"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    retriever = BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)

    with pytest.raises(BM25RetrieverError, match="Tokenizer version mismatch"):
        retriever.initialize()


def test_configuration_mismatch_raises(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["document_count"] = 2
    config_path.write_text(json.dumps(config), encoding="utf-8")
    retriever = BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)

    with pytest.raises(BM25RetrieverError, match="Consistency"):
        retriever.initialize()


def test_deterministic_retrieval(tmp_path: Path) -> None:
    retriever = _retriever(tmp_path)
    retriever.initialize()
    first = retriever.search("developer", top_k=3)
    second = retriever.search("developer", top_k=3)

    assert [result.model_dump() for result in first] == [result.model_dump() for result in second]


def test_non_bm25_pickle_raises(tmp_path: Path) -> None:
    index_path, corpus_path, config_path = _write_bm25(tmp_path)
    index_path.write_bytes(pickle.dumps({"not": "bm25"}))
    retriever = BM25Retriever(index_path, corpus_path, config_path, catalog_path=None)

    with pytest.raises(BM25RetrieverError, match="expected BM25Okapi"):
        retriever.initialize()

