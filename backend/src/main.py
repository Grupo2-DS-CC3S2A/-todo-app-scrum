"""Application factory de FastAPI.

Compone la aplicacion: logging, CORS, routers y handlers de excepciones.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.excepciones.errors import register_exception_handlers
from src.logging_config import configure_logging, get_logger
from src.rutas import votos_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Construye y configura la instancia de ``FastAPI``."""
    configure_logging()
    app: FastAPI = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(votos_router)

    @app.get("/health", tags=["meta"], summary="Health check")
    async def healthcheck() -> dict[str, str]:
        """Endpoint de liveness para orquestadores."""
        return {"status": "ok"}

    logger.info("Aplicacion '%s' inicializada.", settings.app_name)
    return app


app: FastAPI = create_app()
