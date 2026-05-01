"""Configuracion centralizada de la aplicacion.

Carga los parametros de runtime desde variables de entorno con valores por
defecto seguros para desarrollo. Mantener aqui cualquier valor que cambie
entre ambientes (dev / staging / produccion).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Parametros inmutables de la aplicacion."""

    app_name: str = "Mesa de Partes - Voto Electronico Seguro"
    api_version: str = "1.0.0"
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        )
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    ga_population_size: int = int(os.getenv("GA_POPULATION_SIZE", "10"))
    ga_key_length: int = int(os.getenv("GA_KEY_LENGTH", "8"))
    ga_mutation_rate: float = float(os.getenv("GA_MUTATION_RATE", "0.125"))


settings: Settings = Settings()
