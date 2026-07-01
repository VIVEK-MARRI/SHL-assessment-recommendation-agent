"""Loads the embedding model and generates normalised embeddings.

The model is loaded once per process via a module-level singleton so that
downstream code never reloads it for individual assessments.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from sentence_transformers import SentenceTransformer

from retrieval.constants import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL_NAME

if TYPE_CHECKING:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


class EmbeddingModelError(Exception):
    """Raised when the embedding model cannot be loaded or used."""


def get_model() -> SentenceTransformer:
    """Return the module-level singleton embedding model.

    The model is loaded on first call and cached for the lifetime of the
    process.  Subsequent calls return the cached instance without any I/O.

    Returns:
        Loaded SentenceTransformer instance.

    Raises:
        EmbeddingModelError: If the model cannot be loaded.
    """
    global _model  # noqa: PLW0603
    if _model is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL_NAME)
        try:
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as exc:
            raise EmbeddingModelError(
                f"Failed to load embedding model '{EMBEDDING_MODEL_NAME}': {exc}"
            ) from exc
        logger.info("Embedding model loaded successfully.")
    return _model


def generate_embeddings(
    documents: list[str],
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> np.ndarray:
    """Generate L2-normalised embeddings for a list of documents.

    Embeddings are produced in batches and normalised to unit length so
    that inner product equals cosine similarity inside FAISS IndexFlatIP.

    Args:
        documents: Non-empty list of text documents.
        batch_size: Encoding batch size.

    Returns:
        Float32 numpy array of shape (len(documents), embedding_dim).

    Raises:
        EmbeddingModelError: If the model is unavailable, encoding fails, or
            the documents list is empty.
    """
    if not documents:
        raise EmbeddingModelError("documents list must not be empty")

    model = get_model()
    logger.info(
        "Generating embeddings: num_documents=%d batch_size=%d",
        len(documents),
        batch_size,
    )
    try:
        embeddings: np.ndarray = model.encode(
            documents,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
    except Exception as exc:
        raise EmbeddingModelError(f"Embedding generation failed: {exc}") from exc

    logger.info("Embeddings generated: shape=%s dtype=%s", embeddings.shape, embeddings.dtype)
    return embeddings.astype(np.float32)
