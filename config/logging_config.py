"""Centralized logging configuration for the application foundation."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import AppSettings


def configure_logging(settings: AppSettings) -> None:
    """Configure root logger with console and rotating file handlers.

    Args:
        settings: Validated application settings instance.

    Returns:
        None
    """
    log_directory = Path(settings.log_dir)
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file_path = log_directory / settings.log_file

    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, settings.log_level))
    file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance.

    Args:
        name: Logger name, usually ``__name__``.

    Returns:
        Configured logger object.
    """
    return logging.getLogger(name)
