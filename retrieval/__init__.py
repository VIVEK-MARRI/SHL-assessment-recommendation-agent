"""Retrieval package — embedding index and BM25 index public API."""

from __future__ import annotations

from retrieval.bm25_builder import build_bm25_index_pipeline as build_bm25_index
from retrieval.bm25_loader import load_bm25_index
from retrieval.embedding_retriever import EmbeddingRetriever, search_embeddings
from retrieval.index_builder import build_embedding_index
from retrieval.index_loader import load_embedding_index
from retrieval.retrieval_models import RetrievedAssessment

__all__ = [
    "build_embedding_index",
    "load_embedding_index",
    "EmbeddingRetriever",
    "RetrievedAssessment",
    "search_embeddings",
    "build_bm25_index",
    "load_bm25_index",
]
