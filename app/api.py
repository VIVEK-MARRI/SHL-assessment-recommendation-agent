"""FastAPI router: /health and / endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    summary="Service Info",
    tags=["health"],
    response_class=JSONResponse,
)
async def root() -> dict:
    return {
        "service": "SHL Assessment Recommendation Agent",
        "version": "1.0.0",
        "status": "running",
    }


@router.get(
    "/health",
    summary="Health Check",
    tags=["health"],
    response_class=JSONResponse,
)
async def health(request: Request) -> dict:
    container = request.app.state.container
    h = container.hybrid_retriever.health()

    return {
        "status": "healthy",
        "catalog_loaded": True,
        "embedding_index_loaded": h.embedding_ready,
        "bm25_index_loaded": h.bm25_ready,
        "llm_provider": container.llm_provider,
        "version": "1.0.0",
    }
