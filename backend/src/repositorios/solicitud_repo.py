"""Repositorio del agregado Solicitud (HU04).

Define el puerto de salida ``SolicitudRepository`` (Clean Architecture) y
una implementacion en memoria thread-safe apta para desarrollo y pruebas.
La implementacion concreta puede sustituirse por una basada en SQL/NoSQL
sin alterar la capa de servicios, gracias al principio de inversion de
dependencias.

Cumple con el criterio de aceptacion de HU04: "Ingreso a la base de datos
de solicitudes" exponiendo ``guardar`` como punto de entrada de escritura.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from threading import Lock

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


@lru_cache(maxsize=1)
def get_solicitud_repository() -> SolicitudRepository:
    """Provee una instancia singleton del repositorio (DI para FastAPI)."""
    return RepositorioSolicitudEnMemoria()
