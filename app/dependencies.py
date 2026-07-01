from __future__ import annotations

import logging
from pathlib import Path

from agent.catalog_validator import CatalogValidator
from agent.comparison import ComparisonPipeline
from agent.generation import ResponseGenerator
from agent.generation_client import GenerationClient
from agent.llm_client import LLMClientConfig
from agent.prompt_builder import PromptBuilder
from agent.prompt_templates import PromptTemplates
from agent.query_builder import QueryBuilder
from agent.response_builder import ResponseBuilder
from agent.response_catalog import ResponseCatalog
from agent.router import RuleBasedRouter
from agent.state_extraction import StateExtractor
from agent.validator import ResponseValidator
from retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class AppContainer:
    """Single application-wide container of all service singletons.

    Instantiated once at startup; injected into FastAPI endpoints via dependency.
    """

    def __init__(self) -> None:
        logger.info("Initialising AppContainer …")

        # LLM config (shared by both LLM call sites)
        self._llm_config = LLMClientConfig.from_env()

        # Catalog validators / loaders
        self._catalog_validator = CatalogValidator()
        self._response_catalog = ResponseCatalog()

        # Retrieval layer
        self._hybrid_retriever = HybridRetriever()

        # Agent modules
        self._state_extractor = StateExtractor()
        self._router = RuleBasedRouter()
        self._query_builder = QueryBuilder()
        self._comparison_pipeline = ComparisonPipeline()

        templates = PromptTemplates()
        self._prompt_builder = PromptBuilder(templates=templates)

        gen_client = GenerationClient(config=self._llm_config)
        self._response_generator = ResponseGenerator(client=gen_client)
        self._response_validator = ResponseValidator(
            catalog_validator=self._catalog_validator
        )
        self._response_builder = ResponseBuilder(catalog=self._response_catalog)

        # Top-level service
        from app.services.chat_service import ChatService

        self._chat_service = ChatService(
            state_extractor=self._state_extractor,
            router=self._router,
            query_builder=self._query_builder,
            hybrid_retriever=self._hybrid_retriever,
            comparison_pipeline=self._comparison_pipeline,
            prompt_builder=self._prompt_builder,
            response_generator=self._response_generator,
            response_validator=self._response_validator,
            response_builder=self._response_builder,
        )

        logger.info("AppContainer ready.")

    @property
    def chat_service(self):
        return self._chat_service

    @property
    def hybrid_retriever(self) -> HybridRetriever:
        return self._hybrid_retriever

    @property
    def llm_provider(self) -> str:
        return self._llm_config.provider
