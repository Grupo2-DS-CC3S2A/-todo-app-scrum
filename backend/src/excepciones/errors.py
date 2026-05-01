"""Excepciones de dominio y handlers HTTP centralizados."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.logging_config import get_logger

logger = get_logger(__name__)


class DominioVotacionError(Exception):
    """Excepcion base para errores de dominio del modulo de votacion."""

    http_status: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje: str = mensaje


class VotoDuplicadoError(DominioVotacionError):
    """Se intento registrar un voto cuyo hash ya existe."""

    http_status: int = status.HTTP_409_CONFLICT


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers HTTP para las excepciones de dominio.

    Args:
        app: Instancia de ``FastAPI`` sobre la que se registran los handlers.
    """

    @app.exception_handler(DominioVotacionError)
    async def _dominio_handler(
        _request: Request, exc: DominioVotacionError
    ) -> JSONResponse:
        logger.warning("Error de dominio: %s", exc.mensaje)
        return JSONResponse(
            status_code=exc.http_status,
            content={"detail": exc.mensaje, "tipo": exc.__class__.__name__},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Error no controlado: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor."},
        )
