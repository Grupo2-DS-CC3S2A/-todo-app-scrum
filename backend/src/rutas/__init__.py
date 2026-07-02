"""Routers HTTP de la aplicacion."""

from src.rutas.admin_solicitudes import router as admin_solicitudes_router
<<<<<<< HEAD
from src.rutas.votos import router as votos_router
=======
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
from src.rutas.auth import router as auth_router
from src.rutas.validacion import router as validacion_router

__all__ = [
    "admin_solicitudes_router",
    "auth_router",
<<<<<<< HEAD
    "votos_router",
=======
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
    "validacion_router",
]
