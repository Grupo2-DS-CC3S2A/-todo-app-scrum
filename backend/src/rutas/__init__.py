"""Routers HTTP de la aplicacion."""

from src.rutas.admin_solicitudes import router as admin_solicitudes_router
from src.rutas.votos import router as votos_router

__all__ = ["admin_solicitudes_router", "votos_router"]
