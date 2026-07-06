"""Routers HTTP de la aplicacion."""

from src.rutas.admin_solicitudes import router as admin_solicitudes_router
from src.rutas.auth import router as auth_router
from src.rutas.validacion import router as validacion_router
from src.rutas.dependencias import router as dependencias_router
from src.rutas.tramites import router as tramites_router

__all__ = [
    "admin_solicitudes_router",
    "auth_router",
    "validacion_router",
    "dependencias_router",
    "tramites_router",
]