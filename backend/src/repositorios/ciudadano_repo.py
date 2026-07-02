<<<<<<< HEAD
"""Repositorio SQLite para validar ciudadanos de Mesa de Partes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
=======
"""Repositorio Supabase para validar ciudadanos de Mesa de Partes."""

from __future__ import annotations

from typing import Any, cast

from supabase import Client, create_client
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799

from src.config import settings
from src.modelos.ciudadano import CiudadanoValidado


class CiudadanoRepository:
<<<<<<< HEAD
    """Consulta la tabla ``citizens`` de ``validation.db``.

    La base se mantiene como SQLite para respetar el prototipo original de
    MesaParteReniec, pero queda encapsulada detras de un repositorio para que
    el resto del backend conserve la estructura por capas de -todo-app-scrum.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._lock = Lock()

    def _connect(self) -> sqlite3.Connection:
        if not self._db_path.exists():
            raise FileNotFoundError(f"No existe la base SQLite: {self._db_path}")
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
=======
    """Consulta la tabla ``citizens`` en Supabase (migrada desde validation.db).

    Usa la service_role_key para bypasear RLS — la validacion es operacion
    exclusiva del backend, nunca expuesta directamente al cliente.
    """

    def __init__(self) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799

    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        """Devuelve el ciudadano si DNI, digito y fecha coinciden."""
<<<<<<< HEAD
        query = """
            SELECT dni, digit, issue_date, firstname, lastname
            FROM citizens
            WHERE dni = ? AND digit = ? AND issue_date = ?
        """
        with self._lock, self._connect() as conn:
            row = conn.execute(query, (dni, digit, issue_date)).fetchone()
        if row is None:
            return None
=======
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
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
        return CiudadanoValidado(
            dni=str(row["dni"]),
            digit=str(row["digit"]),
            issue_date=str(row["issue_date"]),
            firstname=str(row["firstname"]),
            lastname=str(row["lastname"]),
        )


def get_ciudadano_repository() -> CiudadanoRepository:
<<<<<<< HEAD
    """Fabrica ligera del repositorio SQLite."""
    return CiudadanoRepository(settings.validation_db_path)
=======
    """Fabrica del repositorio Supabase."""
    return CiudadanoRepository()
>>>>>>> b465b534a671ea539fa2e44c93345b99b8c45799
