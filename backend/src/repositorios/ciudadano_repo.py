"""Repositorio Supabase para validar ciudadanos de Mesa de Partes."""

from __future__ import annotations

from typing import Any, cast

from supabase import Client, create_client

from src.config import settings
from src.modelos.ciudadano import CiudadanoValidado


class CiudadanoRepository:
    """Consulta la tabla ``citizens`` en Supabase (migrada desde validation.db).

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
        """Devuelve el ciudadano si DNI, digito y fecha coinciden."""
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


def get_ciudadano_repository() -> CiudadanoRepository:
    """Fabrica del repositorio Supabase."""
    return CiudadanoRepository()