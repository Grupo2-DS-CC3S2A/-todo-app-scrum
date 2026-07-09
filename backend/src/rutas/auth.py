"""Endpoints de autenticacion JWT y ciclo de vida de identidades.

Expone el flujo basico de autenticacion:

- ``POST /api/auth/login``: valida credenciales y emite JWT.
- ``POST /api/auth/register``: alta de usuarios (solo admin).
- ``GET  /api/auth/me``: introspecta el usuario actual.

Y la administracion del ciclo de vida de accesos para admin:

- ``GET   /api/auth/usuarios``: lista usuarios (revision de accesos).
- ``PATCH /api/auth/usuarios/{id}/estado``: activa o revoca el acceso.
- ``PATCH /api/auth/usuarios/{id}/rol``: cambia el rol asignado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.logging_config import get_logger
from src.modelos.usuario import (
    ActualizarEstadoInput,
    ActualizarRolInput,
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
        activo=usuario.activo,
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


@router.get(
    "/usuarios",
    response_model=list[UsuarioPublico],
    summary="Lista todos los usuarios (solo administrador).",
)
async def listar_usuarios(
    auth: AuthService = Depends(get_auth_service),
    _admin: Usuario = Depends(require_admin),
) -> list[UsuarioPublico]:
    """Revision de accesos: quien tiene cuenta, que rol y si esta activa."""
    return [_a_publico(u) for u in auth.listar_usuarios()]


@router.patch(
    "/usuarios/{usuario_id}/estado",
    response_model=UsuarioPublico,
    summary="Activa o revoca el acceso de un usuario (solo administrador).",
)
async def actualizar_estado(
    usuario_id: str,
    payload: ActualizarEstadoInput,
    auth: AuthService = Depends(get_auth_service),
    admin: Usuario = Depends(require_admin),
) -> UsuarioPublico:
    """Revocacion/reactivacion de acceso.

    Efecto inmediato: un token ya emitido para una cuenta desactivada deja
    de ser aceptado en la siguiente peticion (``auth_deps.get_current_user``).
    """
    usuario = auth.actualizar_estado(usuario_id, payload.activo, solicitante=admin)
    return _a_publico(usuario)


@router.patch(
    "/usuarios/{usuario_id}/rol",
    response_model=UsuarioPublico,
    summary="Cambia el rol de un usuario (solo administrador).",
)
async def actualizar_rol(
    usuario_id: str,
    payload: ActualizarRolInput,
    auth: AuthService = Depends(get_auth_service),
    _admin: Usuario = Depends(require_admin),
) -> UsuarioPublico:
    """Cambio de rol dentro del ciclo de vida de la identidad."""
    usuario = auth.actualizar_rol(usuario_id, payload.rol)
    return _a_publico(usuario)
