"""Unit tests for retrieval.embedding_generator."""

from __future__ import annotations

import numpy as np
import pytest

from retrieval.embedding_generator import (
    EmbeddingModelError,
    generate_embeddings,
    get_model,
)


class TestGetModel:
    def test_returns_model(self):
        model = get_model()
        assert model is not None

    def test_singleton(self):
        """Calling get_model() twice returns the exact same object."""
        m1 = get_model()
        m2 = get_model()
        assert m1 is m2


class TestGenerateEmbeddings:
    def test_shape(self):
        docs = ["Hello world", "SHL assessment"]
        embs = generate_embeddings(docs)
        assert embs.ndim == 2
        assert embs.shape[0] == 2

    def test_dtype_float32(self):
        embs = generate_embeddings(["test"])
        assert embs.dtype == np.float32

    def test_normalised(self):
        """L2 norm of each row must be ≈ 1.0 (unit vector)."""
        embs = generate_embeddings(["normalised check"])
        norms = np.linalg.norm(embs, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)

    def test_deterministic(self):
        """Same text must produce identical embeddings on CPU."""
        docs = ["deterministic test document"]
        e1 = generate_embeddings(docs)
        e2 = generate_embeddings(docs)
        np.testing.assert_array_equal(e1, e2)

    def test_empty_raises(self):
        with pytest.raises(EmbeddingModelError, match="empty"):
            generate_embeddings([])

    def test_batch_size_param(self):
        """batch_size kwarg must not break generation."""
        docs = [f"doc {i}" for i in range(10)]
        embs = generate_embeddings(docs, batch_size=3)
        assert embs.shape[0] == 10
