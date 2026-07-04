"""Modelos Pydantic del dominio."""

from src.modelos.solicitud import (
    Dependencia,
    DerivacionInput,
    EstadoSolicitud,
    Solicitud,
    SolicitudDerivada,
    SolicitudInput,
)
from src.modelos.tipo_persona import TipoPersona
from src.modelos.usuario import (
    LoginInput,
    RegistroInput,
    RolUsuario,
    TokenResponse,
    Usuario,
    UsuarioPublico,
)

__all__ = [
    "Dependencia",
    "DerivacionInput",
    "EstadoSolicitud",
    "Solicitud",
    "SolicitudDerivada",
    "SolicitudInput",
    "TipoPersona",
    "LoginInput",
    "RegistroInput",
    "RolUsuario",
    "TokenResponse",
    "Usuario",
    "UsuarioPublico",
]
