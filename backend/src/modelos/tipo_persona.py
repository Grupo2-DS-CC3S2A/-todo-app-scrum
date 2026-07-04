"""Modelo del tipo de persona que origina una solicitud.
Determina si el solicitante es una Persona Natural
por DNI o una Persona Juridica por RUC.
"""

from __future__ import annotations

from enum import Enum


class TipoPersona(str, Enum):
    """Tipos de persona solicitante soportados por Mesa de Partes"""

    NATURAL = "NATURAL"
    JURIDICA = "JURIDICA"
