"""Excepciones de dominio y manejadores HTTP."""

from src.excepciones.errors import (
    CredencialesInvalidasError,
    DominioVotacionError,
    PermisoDenegadoError,
    TokenInvalidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
<<<<<<< HEAD
    VotoDuplicadoError,
=======
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
    register_exception_handlers,
)

__all__ = [
    "CredencialesInvalidasError",
    "DominioVotacionError",
    "PermisoDenegadoError",
    "TokenInvalidoError",
    "UsuarioDuplicadoError",
    "UsuarioNoEncontradoError",
<<<<<<< HEAD
    "VotoDuplicadoError",
=======
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
    "register_exception_handlers",
]
