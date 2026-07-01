"""Application foundation bootstrap entrypoint.

This module initializes typed configuration and centralized logging.
It intentionally excludes business and API logic.
"""

from __future__ import annotations

from config import configure_logging, get_logger, get_settings


def bootstrap() -> None:
    """Initialize foundational runtime components.

    Loads validated settings, configures logging, and emits a startup summary.

    Returns:
        None
    """
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    logger.info("Application foundation initialized")
    logger.info(
        "Runtime context: env=%s app=%s version=%s host=%s port=%s",
        settings.environment,
        settings.app_name,
        settings.app_version,
        settings.host,
        settings.port,
    )


if __name__ == "__main__":
    bootstrap()
