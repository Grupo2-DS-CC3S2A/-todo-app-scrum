"""Configuracion centralizada de logging.

Reemplaza el uso de ``print`` por un logger estructurado. Se llama una sola
vez al construir la aplicacion (idempotente).
"""

from __future__ import annotations

import logging
from logging import Logger

from src.config import settings

_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Configura el logger raiz una sola vez por proceso."""
    root: Logger = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=settings.log_level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )


def get_logger(name: str) -> Logger:
    """Devuelve un logger nombrado siguiendo la jerarquia de modulos."""
    return logging.getLogger(name)
