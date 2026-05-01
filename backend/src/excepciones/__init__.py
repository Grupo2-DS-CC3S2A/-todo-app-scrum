"""Excepciones de dominio y manejadores HTTP."""

from src.excepciones.errors import (
    DominioVotacionError,
    VotoDuplicadoError,
    register_exception_handlers,
)

__all__ = [
    "DominioVotacionError",
    "VotoDuplicadoError",
    "register_exception_handlers",
]
