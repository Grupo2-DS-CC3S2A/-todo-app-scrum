"""Endpoints de autenticacion JWT (S2-05).

Expone el flujo basico de autenticacion:

- ``POST /api/auth/login``: valida credenciales y emite JWT.
- ``POST /api/auth/register``: alta de usuarios (solo admin).
- ``GET  /api/auth/me``: introspecta el usuario actual.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.logging_config import get_logger
from src.modelos.usuario import (
    LoginInput,
    RegistroInput,
    TokenResponse,
    Usuario,
    UsuarioPublico,
)
from src.rutas.auth_deps import get_current_user, require_admin
from src.servicios.auth_service import AuthService, get_auth_service

logger = get_logger(__name__)

router: APIRouter = APIRouter(prefix="/api/auth", tags=["auth"])


def _a_publico(usuario: Usuario) -> UsuarioPublico:
    return UsuarioPublico(
        id=usuario.id,
        username=usuario.username,
        rol=usuario.rol,
        created_at=usuario.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login con username/password. Retorna JWT.",
)
async def login(
    payload: LoginInput,
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Autentica al usuario y devuelve un JWT firmado."""
    return auth.autenticar(payload)


@router.post(
    "/register",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo usuario (solo administrador).",
)
async def register(
    payload: RegistroInput,
    auth: AuthService = Depends(get_auth_service),
    _admin: Usuario = Depends(require_admin),
) -> UsuarioPublico:
    """Registra un nuevo usuario. Requiere JWT de rol admin."""
    usuario = auth.registrar(payload)
    return _a_publico(usuario)


@router.get(
    "/me",
    response_model=UsuarioPublico,
    summary="Devuelve el usuario asociado al token actual.",
)
async def me(
    usuario: Usuario = Depends(get_current_user),
) -> UsuarioPublico:
    """Introspeccion del JWT actual."""
    return _a_publico(usuario)
