"""Funciones de cifrado / hashing para el voto.

Centraliza la construccion del payload y el calculo del digest SHA-256 para
garantizar que el formato sea consistente en todos los puntos del sistema.
"""

from __future__ import annotations

import hashlib
from typing import Final

_SEPARADOR: Final[str] = "|"


def aplicar_hash_sha256(dni: str, candidato: int, llave: str) -> str:
    """Calcula el digest SHA-256 del voto.

    Args:
        dni: DNI del votante (8 digitos validados aguas arriba).
        candidato: Identificador del candidato elegido.
        llave: Llave evolutiva proveniente del algoritmo genetico.

    Returns:
        Digest hexadecimal de 64 caracteres.
    """
    payload: str = f"{dni}{_SEPARADOR}{candidato}{_SEPARADOR}{llave}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
