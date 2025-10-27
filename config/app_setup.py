from __future__ import annotations

import logging

from config.logging_setup import setup_logging
from config.settings import Config

logger = logging.getLogger(__name__)


def setup_application(settings: Config) -> None:
    """Prepare application environment using loaded settings."""
    setup_logging(settings.log_file_path, level=settings.log_level)

    logger.debug(
        "Application setup completed (log_file=%s, log_level=%s)",
        settings.log_file_path,
        settings.LOG_LEVEL,
    )


__all__ = ["setup_application"]
