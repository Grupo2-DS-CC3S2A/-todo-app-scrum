"""Repositorio SQLite para validar ciudadanos de Mesa de Partes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from src.config import settings
from src.modelos.ciudadano import CiudadanoValidado


class CiudadanoRepository:
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

    def buscar_por_credenciales(
        self,
        *,
        dni: str,
        digit: str,
        issue_date: str,
    ) -> CiudadanoValidado | None:
        """Devuelve el ciudadano si DNI, digito y fecha coinciden."""
        query = """
            SELECT dni, digit, issue_date, firstname, lastname
            FROM citizens
            WHERE dni = ? AND digit = ? AND issue_date = ?
        """
        with self._lock, self._connect() as conn:
            row = conn.execute(query, (dni, digit, issue_date)).fetchone()
        if row is None:
            return None
        return CiudadanoValidado(
            dni=str(row["dni"]),
            digit=str(row["digit"]),
            issue_date=str(row["issue_date"]),
            firstname=str(row["firstname"]),
            lastname=str(row["lastname"]),
        )


def get_ciudadano_repository() -> CiudadanoRepository:
    """Fabrica ligera del repositorio SQLite."""
    return CiudadanoRepository(settings.validation_db_path)
