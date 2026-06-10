"""Excepciones de dominio y manejadores HTTP."""

from src.excepciones.errors import (
    CredencialesInvalidasError,
    DominioVotacionError,
    PermisoDenegadoError,
    TokenInvalidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
    VotoDuplicadoError,
    register_exception_handlers,
)

__all__ = [
    "CredencialesInvalidasError",
    "DominioVotacionError",
    "PermisoDenegadoError",
    "TokenInvalidoError",
    "UsuarioDuplicadoError",
    "UsuarioNoEncontradoError",
    "VotoDuplicadoError",
    "register_exception_handlers",
]
