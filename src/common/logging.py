# src/common/logging.py

from __future__ import annotations

import logging
from logging.config import dictConfig

from loguru import logger

from common.config import settings


def _get_log_level() -> str:
    """Нормализуем уровень логов из settings.LOG_LEVEL."""
    level = (settings.LOG_LEVEL or "INFO").upper()
    valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level not in valid:
        level = "INFO"
    return level


def setup_logging() -> None:
    """
    Настройка stdlib-логгера + файловый лог через Loguru.

    - Все стандартные логгеры (наш, uvicorn, fastapi) пишут в stderr
      с единым форматом.
    - Loguru пишет ротационный файл app.log для дебага.
    """
    level = _get_log_level()

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
            },
            "handlers": {
                "stderr": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "loggers": {
                # корневой логгер
                "": {"handlers": ["stderr"], "level": level},
                # наш главный логгер
                "astrodaily": {
                    "handlers": ["stderr"],
                    "level": level,
                    "propagate": False,
                },
                # uvicorn / fastapi
                "uvicorn": {
                    "handlers": ["stderr"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["stderr"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["stderr"],
                    "level": level,
                    "propagate": False,
                },
            },
        }
    )

    # Файловый лог через loguru (ротация по размеру)
    logger.remove()
    logger.add(
        "app.log",
        rotation="10 MB",
        retention="7 days",
        level=level,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    logging.getLogger("astrodaily").info("Logging configured, level=%s", level)
