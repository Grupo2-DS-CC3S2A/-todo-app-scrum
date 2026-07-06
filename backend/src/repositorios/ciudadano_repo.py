"""Repositorio de ciudadanos: puerto, adaptador Supabase y Proxy de cache.

Define el puerto abstracto ``CiudadanoRepository`` (la capa de servicios
depende solo de el), el adaptador concreto ``CiudadanoRepositorySupabase``
que consulta la tabla ``public.citizens`` y un Proxy (Estructural) de
cache que controla el acceso al adaptador remoto.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, cast

from supabase import Client, create_client

from src.config import settings
from src.modelos.ciudadano import CiudadanoValidado

_CACHE_TTL_SEGUNDOS: float = 300.0
_CACHE_MAX_ENTRADAS: int = 256


class CiudadanoRepository(ABC):
    """Puerto de salida para la consulta de ciudadanos registrados."""

    @abstractmethod
    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        """Devuelve el ciudadano si DNI, digito y fecha coinciden."""


class CiudadanoRepositorySupabase(CiudadanoRepository):
    """Adaptador Supabase que consulta la tabla ``public.citizens``.

    Usa la service_role_key para bypasear RLS — la validacion es operacion
    exclusiva del backend, nunca expuesta directamente al cliente.
    """

    def __init__(self) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )

    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        response = (
            self._client.table("citizens")
            .select("dni, digit, issue_date, firstname, lastname")
            .eq("dni", dni)
            .eq("digit", int(digit))  # el digit es int en PostgreSQL
            .eq("issue_date", issue_date)
            .execute()
        )
        if not response.data:
            return None
        row = cast(dict[str, Any], response.data[0])
        return CiudadanoValidado(
            dni=str(row["dni"]),
            digit=str(row["digit"]),
            issue_date=str(row["issue_date"]),
            firstname=str(row["firstname"]),
            lastname=str(row["lastname"]),
        )


class CiudadanoRepositoryCacheProxy(CiudadanoRepository):
    """Proxy (Estructural) de cache sobre el repositorio real.

    Controla el acceso al adaptador remoto: una validacion ya resuelta
    dentro de la ventana TTL se responde desde memoria sin viajar a
    Supabase. Solo cachea aciertos — un intento fallido NO se cachea,
    para que un ciudadano recien sembrado en la tabla valide de
    inmediato sin esperar a que expire una entrada negativa.

    Mismo contrato ``CiudadanoRepository`` que el objeto real: la capa
    de servicios no distingue si habla con el proxy o con Supabase.
    """

    def __init__(
        self,
        real: CiudadanoRepository,
        ttl_segundos: float = _CACHE_TTL_SEGUNDOS,
        max_entradas: int = _CACHE_MAX_ENTRADAS,
    ) -> None:
        self._real = real
        self._ttl = ttl_segundos
        self._max = max_entradas
        self._cache: dict[tuple[str, str, str], tuple[float, CiudadanoValidado]] = {}
        self._lock = Lock()

    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        llave = (dni, digit, issue_date)
        ahora = time.monotonic()

        with self._lock:
            entrada = self._cache.get(llave)
            if entrada is not None:
                registrado_en, ciudadano = entrada
                if ahora - registrado_en < self._ttl:
                    return ciudadano
                del self._cache[llave]

        resultado = self._real.buscar_por_credenciales(
            dni=dni,
            digit=digit,
            issue_date=issue_date,
        )
        if resultado is not None:
            with self._lock:
                if len(self._cache) >= self._max:
                    self._purgar_expiradas(ahora)
                if len(self._cache) >= self._max:
                    # Sigue llena tras purgar: descarta la entrada mas antigua.
                    self._cache.pop(next(iter(self._cache)))
                self._cache[llave] = (ahora, resultado)
        return resultado

    def _purgar_expiradas(self, ahora: float) -> None:
        vencidas = [
            llave
            for llave, (registrado_en, _) in self._cache.items()
            if ahora - registrado_en >= self._ttl
        ]
        for llave in vencidas:
            del self._cache[llave]


def get_ciudadano_repository() -> CiudadanoRepository:
    """Fabrica del repositorio: adaptador Supabase detras del Proxy de cache."""
    return CiudadanoRepositoryCacheProxy(CiudadanoRepositorySupabase())


__all__ = [
    "CiudadanoRepository",
    "CiudadanoRepositorySupabase",
    "CiudadanoRepositoryCacheProxy",
    "get_ciudadano_repository",
]
