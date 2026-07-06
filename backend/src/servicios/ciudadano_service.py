"""Servicio de dominio para validacion de acceso ciudadano."""

from __future__ import annotations

from functools import lru_cache

from src.modelos.ciudadano import (
    ValidacionCiudadanoInput,
    ValidacionCiudadanoResponse,
)
from src.repositorios.ciudadano_repo import CiudadanoRepository


class CiudadanoService:
    """Orquesta la validacion de ingreso contra la tabla ``citizens``."""

    def __init__(self, repositorio: CiudadanoRepository) -> None:
        self._repositorio = repositorio

    def validar(
        self,
        payload: ValidacionCiudadanoInput,
    ) -> ValidacionCiudadanoResponse:
        """Valida DNI, digito y fecha de emision contra Supabase."""
        ciudadano = self._repositorio.buscar_por_credenciales(
            dni=payload.dni,
            digit=payload.digit,
            issue_date=payload.date,
        )
        if ciudadano is None:
            return ValidacionCiudadanoResponse(valid=False)
        return ValidacionCiudadanoResponse(
            valid=True,
            dni=ciudadano.dni,
            firstname=ciudadano.firstname,
            lastname=ciudadano.lastname,
        )


@lru_cache(maxsize=1)
def get_ciudadano_service() -> CiudadanoService:
    """Dependency provider para FastAPI (singleton).

    Sin ``lru_cache`` cada request construia un cliente Supabase nuevo y
    el Proxy de cache nacia vacio en cada llamada, anulando su efecto.
    """
    from src.repositorios.ciudadano_repo import get_ciudadano_repository

    return CiudadanoService(get_ciudadano_repository())
