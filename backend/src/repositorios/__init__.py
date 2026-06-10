"""Capa de repositorios (puertos de salida).

Aisla la persistencia detras de interfaces abstractas para que la capa de
servicios dependa de abstracciones (DIP). Las implementaciones concretas
(en memoria, SQL, etc.) se inyectan en runtime.
"""

from src.repositorios.solicitud_repo import (
    RepositorioSolicitudEnMemoria,
    SolicitudRepository,
    get_solicitud_repository,
)
from src.repositorios.usuario_repo import (
    RepositorioUsuarioEnMemoria,
    UsuarioRepository,
    get_usuario_repository,
)

__all__ = [
    "RepositorioSolicitudEnMemoria",
    "SolicitudRepository",
    "get_solicitud_repository",
    "RepositorioUsuarioEnMemoria",
    "UsuarioRepository",
    "get_usuario_repository",
]
