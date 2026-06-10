"""Repositorio del agregado Usuario (S2-05).

Define el puerto ``UsuarioRepository`` y una implementacion en memoria
thread-safe (Singleton GoF) que sustituye temporalmente a la futura
implementacion SQLAlchemy (S2-01). Permite las operaciones minimas que
requiere el flujo de autenticacion JWT: registrar, buscar por username
o id, y listar.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from threading import Lock

from src.excepciones.errors import (
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
)
from src.logging_config import get_logger
from src.modelos.usuario import Usuario

logger = get_logger(__name__)


class UsuarioRepository(ABC):
    """Puerto de salida para la persistencia de usuarios."""

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        """Persiste un nuevo usuario.

        Raises:
            UsuarioDuplicadoError: Si username ya existe.
        """

    @abstractmethod
    def obtener_por_username(self, username: str) -> Usuario:
        """Recupera un usuario por username.

        Raises:
            UsuarioNoEncontradoError: Si no existe.
        """

    @abstractmethod
    def obtener_por_id(self, usuario_id: str) -> Usuario:
        """Recupera un usuario por id.

        Raises:
            UsuarioNoEncontradoError: Si no existe.
        """

    @abstractmethod
    def existe_username(self, username: str) -> bool:
        """Indica si un username ya esta registrado."""

    @abstractmethod
    def listar(self) -> list[Usuario]:
        """Lista todos los usuarios persistidos."""


class RepositorioUsuarioEnMemoria(UsuarioRepository):
    """Adaptador en memoria thread-safe (GoF Singleton)."""

    _instance = None
    _singleton_lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super(
                        RepositorioUsuarioEnMemoria, cls
                    ).__new__(cls)
                    cls._instance._inicializado = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_inicializado", False):
            return
        self._por_id: dict[str, Usuario] = {}
        self._por_username: dict[str, str] = {}
        self._lock: Lock = Lock()
        self._inicializado = True

    def guardar(self, usuario: Usuario) -> Usuario:
        with self._lock:
            if usuario.username in self._por_username:
                raise UsuarioDuplicadoError(
                    f"El username '{usuario.username}' ya esta registrado."
                )
            if usuario.id in self._por_id:
                raise UsuarioDuplicadoError(
                    f"El usuario id '{usuario.id}' ya existe."
                )
            self._por_id[usuario.id] = usuario
            self._por_username[usuario.username] = usuario.id
        logger.info(
            "Usuario persistido | id=%s | username=%s | rol=%s",
            usuario.id,
            usuario.username,
            usuario.rol.value,
        )
        return usuario

    def obtener_por_username(self, username: str) -> Usuario:
        with self._lock:
            usuario_id = self._por_username.get(username)
            usuario = self._por_id.get(usuario_id) if usuario_id else None
        if usuario is None:
            raise UsuarioNoEncontradoError(
                f"No existe usuario con username '{username}'."
            )
        return usuario

    def obtener_por_id(self, usuario_id: str) -> Usuario:
        with self._lock:
            usuario = self._por_id.get(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontradoError(
                f"No existe usuario con id '{usuario_id}'."
            )
        return usuario

    def existe_username(self, username: str) -> bool:
        with self._lock:
            return username in self._por_username

    def listar(self) -> list[Usuario]:
        with self._lock:
            return list(self._por_id.values())


@lru_cache(maxsize=1)
def get_usuario_repository() -> UsuarioRepository:
    """Provee una instancia del repositorio singleton de usuarios."""
    return RepositorioUsuarioEnMemoria()
