"""Application factory de FastAPI.

Compone la aplicacion: logging, CORS, routers y handlers de excepciones.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.excepciones.errors import register_exception_handlers
from src.logging_config import configure_logging, get_logger
from src.repositorios.solicitud_repo import get_solicitud_repository
from src.rutas import (
    admin_solicitudes_router,
    auth_router,
    validacion_router,
)

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
    app.include_router(auth_router)
    app.include_router(validacion_router)
    app.include_router(admin_solicitudes_router)

    @app.get("/health", tags=["meta"], summary="Health check con base de datos")
    async def healthcheck(repo=Depends(get_solicitud_repository)) -> dict:
        """Endpoint de liveness y readiness para orquestadores."""
        try:
            await repo.ping_database()

            return {"status": "ok", "database": "connected"}
        except Exception as e:
            logger.error(f"Error de conexión a la base de datos: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "error", "database": "disconnected"},
            )

    logger.info("Aplicacion '%s' inicializada.", settings.app_name)
    return app


app: FastAPI = create_app()
