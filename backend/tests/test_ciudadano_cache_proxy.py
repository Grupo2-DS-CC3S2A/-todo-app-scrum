"""Tests del Proxy de cache sobre ``CiudadanoRepository``."""

from __future__ import annotations

from src.modelos.ciudadano import CiudadanoValidado
from src.repositorios.ciudadano_repo import (
    CiudadanoRepository,
    CiudadanoRepositoryCacheProxy,
)

_CREDENCIALES_OK = {"dni": "40392536", "digit": "1", "issue_date": "2024-07-25"}


class RepoContador(CiudadanoRepository):
    """Repositorio falso que cuenta cuantas veces se consulta el 'remoto'."""

    def __init__(self) -> None:
        self.llamadas = 0

    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        self.llamadas += 1
        if dni == _CREDENCIALES_OK["dni"]:
            return CiudadanoValidado(
                dni=dni,
                digit=digit,
                issue_date=issue_date,
                firstname="CESAR",
                lastname="LOPEZ ARTEAGA",
            )
        return None


def test_acierto_repetido_se_sirve_desde_cache() -> None:
    real = RepoContador()
    proxy = CiudadanoRepositoryCacheProxy(real, ttl_segundos=60.0)

    primero = proxy.buscar_por_credenciales(**_CREDENCIALES_OK)
    segundo = proxy.buscar_por_credenciales(**_CREDENCIALES_OK)

    assert primero is not None and segundo is not None
    assert primero == segundo
    assert real.llamadas == 1  # la segunda consulta no viajo al remoto


def test_fallo_no_se_cachea() -> None:
    """Un DNI inexistente debe validar apenas se siembre en la tabla."""
    real = RepoContador()
    proxy = CiudadanoRepositoryCacheProxy(real, ttl_segundos=60.0)
    credenciales = {"dni": "99999999", "digit": "9", "issue_date": "2020-01-01"}

    assert proxy.buscar_por_credenciales(**credenciales) is None
    assert proxy.buscar_por_credenciales(**credenciales) is None
    assert real.llamadas == 2  # ambas consultas fueron al remoto


def test_entrada_expirada_vuelve_al_remoto() -> None:
    real = RepoContador()
    proxy = CiudadanoRepositoryCacheProxy(real, ttl_segundos=0.0)

    proxy.buscar_por_credenciales(**_CREDENCIALES_OK)
    proxy.buscar_por_credenciales(**_CREDENCIALES_OK)

    assert real.llamadas == 2  # TTL 0: toda entrada nace vencida


def test_capacidad_maxima_desaloja_la_entrada_mas_antigua() -> None:
    real = RepoContador()
    proxy = CiudadanoRepositoryCacheProxy(real, ttl_segundos=60.0, max_entradas=1)
    otras = {"dni": "40392536", "digit": "2", "issue_date": "2022-01-01"}

    proxy.buscar_por_credenciales(**_CREDENCIALES_OK)  # llena la cache
    proxy.buscar_por_credenciales(**otras)  # desaloja la anterior
    proxy.buscar_por_credenciales(**_CREDENCIALES_OK)  # vuelve al remoto

    assert real.llamadas == 3
