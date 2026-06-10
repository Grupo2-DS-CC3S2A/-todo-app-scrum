"""Modelos Pydantic del agregado Usuario (S2-05).

Define la entidad ``Usuario`` y los DTOs del flujo de autenticacion JWT:
``LoginInput``, ``RegistroInput`` y ``TokenResponse``. Las contrasenas
nunca se exponen en estos modelos: solo el ``password_hash`` viaja en la
entidad persistible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

USERNAME_MIN_LENGTH: int = 3
USERNAME_MAX_LENGTH: int = 32
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_MAX_LENGTH: int = 128


class RolUsuario(str, Enum):
    """Roles soportados por el sistema."""

    ADMIN = "admin"
    OPERADOR = "operador"
    CIUDADANO = "ciudadano"


def _ahora_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _nuevo_id() -> str:
    return uuid4().hex


class Usuario(BaseModel):
    """Entidad de dominio persistible para un usuario del sistema."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    id: Annotated[str, Field(default_factory=_nuevo_id)]
    username: Annotated[
        str,
        Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH),
    ]
    password_hash: Annotated[str, Field(min_length=1)]
    rol: RolUsuario = RolUsuario.CIUDADANO
    created_at: Annotated[datetime, Field(default_factory=_ahora_utc)]


class UsuarioPublico(BaseModel):
    """Vista publica sin hash de contrasena."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    username: str
    rol: RolUsuario
    created_at: datetime


class LoginInput(BaseModel):
    """Payload del endpoint POST /api/auth/login."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: Annotated[
        str,
        Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH),
    ]
    password: Annotated[
        str,
        Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    ]


class RegistroInput(BaseModel):
    """Payload del endpoint POST /api/auth/register (solo admin)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: Annotated[
        str,
        Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH),
    ]
    password: Annotated[
        str,
        Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    ]
    rol: RolUsuario = RolUsuario.OPERADOR


class TokenResponse(BaseModel):
    """Respuesta estandar OAuth2 simplificada con JWT."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int
