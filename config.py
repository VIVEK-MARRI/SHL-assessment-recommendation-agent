"""Compatibility layer exporting centralized application settings and logger setup."""

from config import AppSettings, configure_logging, get_logger, get_settings

__all__ = [
    "AppSettings",
    "configure_logging",
    "get_logger",
    "get_settings",
]
