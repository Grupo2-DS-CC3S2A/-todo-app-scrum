"""Repositorio del agregado Usuario (S2-05 / MDP-54).

Define el puerto ``UsuarioRepository``, el adaptador en memoria
thread-safe (conservado para tests) y el adaptador Supabase que escribe
en la tabla ``public.usuarios`` de PostgreSQL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from threading import Lock
from typing import Any, cast

from supabase import Client, create_client

from src.config import settings
from src.excepciones.errors import (
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
)
from src.logging_config import get_logger
from src.modelos.usuario import RolUsuario, Usuario

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
                    cls._instance = super(RepositorioUsuarioEnMemoria, cls).__new__(cls)
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
                raise UsuarioDuplicadoError(f"El usuario id '{usuario.id}' ya existe.")
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
            raise UsuarioNoEncontradoError(f"No existe usuario con id '{usuario_id}'.")
        return usuario

    def existe_username(self, username: str) -> bool:
        with self._lock:
            return username in self._por_username

    def listar(self) -> list[Usuario]:
        with self._lock:
            return list(self._por_id.values())


class RepositorioUsuarioSupabase(UsuarioRepository):
    """Adaptador Supabase que persiste en public.usuarios (MDP-54)

    Usa service_role_key para hacer bypass de RLS, por lo que
    sólo lo consume FastAPI, nunca el cliente web directamente.
    """

    def __init__(self) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )

    def guardar(self, usuario: Usuario) -> Usuario:
        try:
            self._client.table("usuarios").insert(
                {
                    "id": usuario.id,
                    "username": usuario.username,
                    "password_hash": usuario.password_hash,
                    "rol": usuario.rol.value,
                    "created_at": usuario.created_at.isoformat(),
                }
            ).execute()
        except Exception as exc:
            if "23505" in str(exc) or "duplicate" in str(exc).lower():
                raise UsuarioDuplicadoError(
                    f"El username '{usuario.username}' ya esta registrado."
                ) from exc
            raise
        logger.info(
            "Usuario persistido en Supabase | id=%s | username=%s | rol=%s",
            usuario.id,
            usuario.username,
            usuario.rol.value,
        )
        return usuario

    def obtener_por_username(self, username: str) -> Usuario:
        response = (
            self._client.table("usuarios")
            .select("*")
            .eq("username", username)
            .limit(1)
            .execute()
        )
        if not response.data:
            raise UsuarioNoEncontradoError(
                f"No existe usuario con username '{username}'."
            )
        return self._fila_a_usuario(cast(dict[str, Any], response.data[0]))

    def obtener_por_id(self, usuario_id: str) -> Usuario:
        response = (
            self._client.table("usuarios")
            .select("*")
            .eq("id", usuario_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            raise UsuarioNoEncontradoError(f"No existe usuario con id '{usuario_id}'.")
        return self._fila_a_usuario(cast(dict[str, Any], response.data[0]))

    def existe_username(self, username: str) -> bool:
        response = (
            self._client.table("usuarios")
            .select("id")
            .eq("username", username)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def listar(self) -> list[Usuario]:
        response = self._client.table("usuarios").select("*").execute()
        return [
            self._fila_a_usuario(cast(dict[str, Any], row)) for row in response.data
        ]

    @staticmethod
    def _fila_a_usuario(row: dict[str, Any]) -> Usuario:
        return Usuario(
            id=str(row["id"]),
            username=str(row["username"]),
            password_hash=str(row["password_hash"]),
            rol=RolUsuario(str(row["rol"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )


def get_usuario_repository() -> UsuarioRepository:
    """Provee el repositorio Supabase de usuarios."""
    return RepositorioUsuarioSupabase()
