"""Repositorio del agregado Solicitud (MDP-54).

Define el puerto SolicitudRepository, el adaptador en memoria
thread-safe sólo para tests y el adaptador Supabase que escribe
en la tabla public.solicitudes de PostgreSQL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from threading import Lock
from typing import Any, cast

from postgrest import CountMethod
from supabase import Client, create_client

from src.config import settings
from src.excepciones.errors import (
    SolicitudDuplicadaError,
    SolicitudNoEncontradaError,
)
from src.logging_config import get_logger
from src.modelos.solicitud import Dependencia, EstadoSolicitud, Solicitud

logger = get_logger(__name__)


class SolicitudRepository(ABC):
    """Puerto de salida para la persistencia de solicitudes.

    La capa de servicios depende unicamente de esta abstraccion. Cualquier
    adaptador concreto (en memoria, SQLAlchemy, MongoDB, etc.) debe honrar
    este contrato.
    """

    @abstractmethod
    def guardar(self, solicitud: Solicitud) -> Solicitud:
        """Persiste una nueva solicitud.

        Args:
            solicitud: Entidad de dominio a persistir.

        Returns:
            La misma entidad ya almacenada (facilita encadenamiento).

        Raises:
            SolicitudDuplicadaError: Si el ``id`` ya existe en el repositorio.
        """

    @abstractmethod
    def obtener_por_id(self, solicitud_id: str) -> Solicitud:
        """Recupera una solicitud por su identificador.

        Raises:
            SolicitudNoEncontradaError: Si no existe ninguna solicitud con
                el ``id`` indicado.
        """

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> list[Solicitud]:
        """Lista todas las solicitudes emitidas por un usuario."""

    @abstractmethod
    def listar_por_dependencia(self, dependencia: Dependencia) -> list[Solicitud]:
        """Lista todas las solicitudes asignadas a una dependencia."""

    @abstractmethod
    def listar_por_estado(self, estado: EstadoSolicitud) -> list[Solicitud]:
        """Lista todas las solicitudes en un estado dado."""

    @abstractmethod
    def listar_todas(self) -> list[Solicitud]:
        """Devuelve todas las solicitudes almacenadas (lectura completa)."""

    @abstractmethod
    def contar(self) -> int:
        """Devuelve la cantidad total de solicitudes persistidas."""


class RepositorioSolicitudEnMemoria(SolicitudRepository):
    """Adaptador en memoria thread-safe del repositorio de solicitudes.

    Apto para desarrollo y pruebas; en produccion se reemplaza por una
    implementacion respaldada por una base de datos relacional. La
    estructura interna usa un diccionario indexado por ``id`` para garantizar
    busqueda O(1) y evitar duplicados.
    """

    def __init__(self) -> None:
        self._solicitudes: dict[str, Solicitud] = {}
        self._lock: Lock = Lock()

    def guardar(self, solicitud: Solicitud) -> Solicitud:
        with self._lock:
            if solicitud.id in self._solicitudes:
                raise SolicitudDuplicadaError(
                    f"La solicitud '{solicitud.id}' ya existe."
                )
            self._solicitudes[solicitud.id] = solicitud
        logger.info(
            "Solicitud persistida | id=%s | dependencia=%s | estado=%s",
            solicitud.id,
            solicitud.dependencia_asignada.value,
            solicitud.estado.value,
        )
        return solicitud

    def obtener_por_id(self, solicitud_id: str) -> Solicitud:
        with self._lock:
            solicitud: Solicitud | None = self._solicitudes.get(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(
                f"No existe solicitud con id '{solicitud_id}'."
            )
        return solicitud

    def listar_por_usuario(self, usuario_id: str) -> list[Solicitud]:
        with self._lock:
            return [s for s in self._solicitudes.values() if s.usuario_id == usuario_id]

    def listar_por_dependencia(self, dependencia: Dependencia) -> list[Solicitud]:
        with self._lock:
            return [
                s
                for s in self._solicitudes.values()
                if s.dependencia_asignada == dependencia
            ]

    def listar_por_estado(self, estado: EstadoSolicitud) -> list[Solicitud]:
        with self._lock:
            return [s for s in self._solicitudes.values() if s.estado == estado]

    def listar_todas(self) -> list[Solicitud]:
        with self._lock:
            return list(self._solicitudes.values())

    def contar(self) -> int:
        with self._lock:
            return len(self._solicitudes)


class RepositorioSolicitudSupabase(SolicitudRepository):
    """Adaptador Supabase que persiste en public.solicitudes (MDP-54).

    Usa service_role_key para hacer bypass de RLS:
    - usuario_id           -> ciudadano_id text
    - dependencia_asignada -> dependencia_asignada text(valor del enum)
    - estado               -> estado estado_solicitud(valor del enum)
    - id (hex)             -> columna uuid para ambos formatos en PostgreSQL
    """

    def __init__(self) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )

    def guardar(self, solicitud: Solicitud) -> Solicitud:
        try:
            self._client.table("solicitudes").insert(
                {
                    "id": solicitud.id,
                    "ciudadano_id": solicitud.usuario_id,
                    "detalle_solicitud": solicitud.detalle_solicitud,
                    "dependencia_asignada": solicitud.dependencia_asignada.value,
                    "fecha_ingreso": solicitud.fecha_ingreso.isoformat(),
                    "fecha_maxima_respuesta": (
                        solicitud.fecha_maxima_respuesta.isoformat()
                    ),
                    "estado": solicitud.estado.value,
                }
            ).execute()
        except Exception as exc:
            if "23505" in str(exc) or "duplicate" in str(exc).lower():
                raise SolicitudDuplicadaError(
                    f"La solicitud '{solicitud.id}' ya existe."
                ) from exc
            raise
        logger.info(
            "Solicitud persistida en Supabase | id=%s | dependencia=%s | estado=%s",
            solicitud.id,
            solicitud.dependencia_asignada.value,
            solicitud.estado.value,
        )
        return solicitud

    def obtener_por_id(self, solicitud_id: str) -> Solicitud:
        response = (
            self._client.table("solicitudes")
            .select("*")
            .eq("id", solicitud_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            raise SolicitudNoEncontradaError(
                f"No existe solicitud con id '{solicitud_id}'."
            )
        return self._fila_a_solicitud(cast(dict[str, Any], response.data[0]))

    def listar_por_usuario(self, usuario_id: str) -> list[Solicitud]:
        response = (
            self._client.table("solicitudes")
            .select("*")
            .eq("ciudadano_id", usuario_id)
            .execute()
        )
        return [
            self._fila_a_solicitud(cast(dict[str, Any], row)) for row in response.data
        ]

    def listar_por_dependencia(self, dependencia: Dependencia) -> list[Solicitud]:
        response = (
            self._client.table("solicitudes")
            .select("*")
            .eq("dependencia_asignada", dependencia.value)
            .execute()
        )
        return [
            self._fila_a_solicitud(cast(dict[str, Any], row)) for row in response.data
        ]

    def listar_por_estado(self, estado: EstadoSolicitud) -> list[Solicitud]:
        response = (
            self._client.table("solicitudes")
            .select("*")
            .eq("estado", estado.value)
            .execute()
        )
        return [
            self._fila_a_solicitud(cast(dict[str, Any], row)) for row in response.data
        ]

    def listar_todas(self) -> list[Solicitud]:
        response = self._client.table("solicitudes").select("*").execute()
        return [
            self._fila_a_solicitud(cast(dict[str, Any], row)) for row in response.data
        ]

    def contar(self) -> int:
        response = (
            self._client.table("solicitudes")
            .select("id", count=CountMethod.exact)
            .execute()
        )
        return response.count or 0

    @staticmethod
    def _fila_a_solicitud(row: dict[str, Any]) -> Solicitud:
        return Solicitud(
            id=str(row["id"]).replace("-", ""),
            usuario_id=str(row["ciudadano_id"]),
            detalle_solicitud=str(row["detalle_solicitud"]),
            dependencia_asignada=Dependencia(str(row["dependencia_asignada"])),
            fecha_ingreso=datetime.fromisoformat(str(row["fecha_ingreso"])),
            fecha_maxima_respuesta=datetime.fromisoformat(
                str(row["fecha_maxima_respuesta"])
            ),
            estado=EstadoSolicitud(str(row["estado"])),
        )


@lru_cache(maxsize=1)
def get_solicitud_repository() -> SolicitudRepository:
    """Provee una instancia singleton del repositorio (DI para FastAPI)."""
    return RepositorioSolicitudEnMemoria()
