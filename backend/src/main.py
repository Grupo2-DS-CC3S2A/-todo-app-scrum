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
    dependencias_router,
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
    app.include_router(dependencias_router)

    @app.get("/health", tags=["meta"], summary="Health check")
    async def healthcheck() -> dict[str, str]:
        """Verifica liveness y que la conexion a Supabase responda.

        La construccion del cliente Supabase (credenciales invalidas,
        host inalcanzable) tambien debe reportarse como 503, por lo que
        se resuelve dentro del ``try`` en vez de inyectarse via
        ``Depends`` (que fallaria antes de llegar aqui).
        """
        try:
            get_solicitud_repository().contar()
        except Exception as exc:
            logger.error("Health check fallo: Supabase no responde. %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo conectar a Supabase.",
            ) from exc
        return {"status": "ok"}

    logger.info("Aplicacion '%s' inicializada.", settings.app_name)
    return app


app: FastAPI = create_app()
