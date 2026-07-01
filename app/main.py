"""FastAPI application factory with lifespan, middleware, and exception handlers."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from agent.response_models import ChatResponse
from app.api import router as health_router
from app.schemas import ChatRequest

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting up SHL Assessment Recommendation Agent …")

    # Allow tests to pre-inject a mock container before lifespan runs
    if not hasattr(app.state, "container"):
        from app.dependencies import AppContainer

        container = AppContainer()
        container.hybrid_retriever.initialize()
        app.state.container = container

    logger.info("Startup complete.")

    yield

    # Shutdown: nothing persistent to release in this sync stack
    logger.info("Shutting down …")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SHL Assessment Recommendation Agent",
        description=(
            "Conversational API for recommending SHL Individual Test Solutions "
            "using hybrid retrieval and grounded LLM generation."
        ),
        version="1.0.0",
        openapi_tags=[
            {"name": "health", "description": "Service status and readiness checks."},
            {"name": "chat", "description": "Conversational recommendation endpoint."},
        ],
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        logger.info(
            "Request started: method=%s path=%s request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )
        import time
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Request completed: method=%s path=%s status=%d latency_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Exception handlers ──────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error. Please try again later."},
        )

    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    # ── Routes ──────────────────────────────────────────────────────────────
    app.include_router(health_router)

    @app.post(
        "/chat",
        response_model=ChatResponse,
        summary="Chat",
        description="Send a conversation history and receive an assessment recommendation or clarification.",
        tags=["chat"],
        responses={
            400: {"description": "Bad request — invalid message list"},
            422: {"description": "Validation error — malformed request body"},
            429: {"description": "Rate limit exceeded"},
            500: {"description": "Internal server error"},
            503: {"description": "LLM provider unavailable"},
        },
    )
    async def chat_endpoint(request_body: ChatRequest, request: Request) -> ChatResponse:
        from agent.generation_client import RateLimitError, ProviderError
        from agent.validator import InvalidGenerationResult

        container = request.app.state.container

        if not request_body.messages:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "messages must not be empty."},
            )

        try:
            return container.chat_service.chat(request_body.messages)

        except RateLimitError as exc:
            logger.warning("Rate limit from provider: %s", exc)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "LLM provider rate limit exceeded. Please retry shortly."},
            )
        except ProviderError as exc:
            logger.error("LLM provider error: %s", exc)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "LLM provider is temporarily unavailable."},
            )
        except InvalidGenerationResult as exc:
            logger.error("Validation failed: %s", exc)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Response generation failed. Please try again."},
            )
        except Exception as exc:
            logger.error("Unexpected error in /chat: %s", exc, exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error. Please try again later."},
            )

    return app


app = create_app()
