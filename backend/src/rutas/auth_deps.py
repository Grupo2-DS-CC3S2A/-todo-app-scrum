"""Dependencias FastAPI para autenticacion y autorizacion JWT (S2-05).

Provee tres helpers reutilizables:

- ``get_current_user``: extrae y valida el JWT del header ``Authorization``
  y resuelve el ``Usuario`` actual contra el repositorio.
- ``require_admin``: garantiza que el usuario actual tiene rol admin.
- ``require_roles``: factory que produce una dependencia para cualquier
  conjunto de roles permitidos.
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.excepciones.errors import (
    PermisoDenegadoError,
    TokenInvalidoError,
    UsuarioNoEncontradoError,
)
from src.modelos.usuario import RolUsuario, Usuario
from src.servicios.auth_service import AuthService, get_auth_service

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth: AuthService = Depends(get_auth_service),
) -> Usuario:
    """Resuelve el usuario autenticado a partir del JWT Bearer.

    Raises:
        TokenInvalidoError: 401 si no hay token, esta malformado o expiro.
    """
    if credentials is None or not credentials.credentials:
        raise TokenInvalidoError("Se requiere un token de acceso.")
    payload = auth.decodificar_token(credentials.credentials)
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise TokenInvalidoError("Token sin claim 'sub'.")
    try:
        return auth.obtener_usuario(usuario_id)
    except UsuarioNoEncontradoError as exc:
        raise TokenInvalidoError("El usuario del token ya no existe.") from exc


def require_roles(*roles: RolUsuario):
    """Factory de dependencia: exige uno de los roles dados."""
    allowed: tuple[RolUsuario, ...] = roles

    async def _checker(
        usuario: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if usuario.rol not in allowed:
            raise PermisoDenegadoError("El usuario no tiene permisos suficientes.")
        return usuario

    return _checker


require_admin = require_roles(RolUsuario.ADMIN)
