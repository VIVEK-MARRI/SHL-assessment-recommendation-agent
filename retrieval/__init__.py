"""Retrieval package — embedding index and BM25 index public API."""

from __future__ import annotations

from retrieval.bm25_builder import build_bm25_index_pipeline as build_bm25_index
from retrieval.bm25_loader import load_bm25_index
from retrieval.bm25_retriever import BM25Retriever, search_bm25
from retrieval.confidence_gate import ConfidenceGate, ConfidenceGateError
from retrieval.embedding_retriever import EmbeddingRetriever, search_embeddings
from retrieval.hybrid_retriever import HybridRetriever, HybridRetrieverError
from retrieval.index_builder import build_embedding_index
from retrieval.index_loader import load_embedding_index
from retrieval.reciprocal_rank_fusion import RRFError, reciprocal_rank_fusion
from retrieval.retrieval_models import HybridRetrievalResult, HybridRetrieverHealth, RetrievedAssessment

__all__ = [
    "build_embedding_index",
    "load_embedding_index",
    "EmbeddingRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "HybridRetrieverError",
    "HybridRetrievalResult",
    "HybridRetrieverHealth",
    "ConfidenceGate",
    "ConfidenceGateError",
    "RRFError",
    "RetrievedAssessment",
    "reciprocal_rank_fusion",
    "search_embeddings",
    "search_bm25",
    "build_bm25_index",
    "load_bm25_index",
]
