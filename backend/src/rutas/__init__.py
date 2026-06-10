"""Routers HTTP de la aplicacion."""

from src.rutas.admin_solicitudes import router as admin_solicitudes_router
from src.rutas.votos import router as votos_router
from src.rutas.auth import router as auth_router

__all__ = [
    "admin_solicitudes_router",
    "auth_router",
    "votos_router",
]
