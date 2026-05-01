"""Modelos Pydantic del dominio de votacion.

Define los DTOs que entran y salen de la API. Las validaciones estrictas se
aplican aqui (formato y longitud de DNI, rango de id de candidato).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

DNI_LENGTH: int = 8


class VotoInput(BaseModel):
    """Payload de entrada para registrar un voto."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dni_votante: Annotated[
        str,
        Field(
            min_length=DNI_LENGTH,
            max_length=DNI_LENGTH,
            pattern=r"^\d{8}$",
            description="DNI peruano: exactamente 8 digitos numericos.",
            examples=["12345678"],
        ),
    ]
    id_candidato: Annotated[
        int,
        Field(ge=1, le=9999, description="Identificador unico del candidato."),
    ]

    @field_validator("dni_votante")
    @classmethod
    def _dni_no_repetido(cls, valor: str) -> str:
        """Rechaza DNIs triviales como '00000000' o '11111111'."""
        if len(set(valor)) == 1:
            raise ValueError("DNI invalido: no se admiten digitos repetidos.")
        return valor


class VotoCifrado(BaseModel):
    """Comprobante anonimo emitido tras cifrar un voto."""

    model_config = ConfigDict(extra="forbid")

    hash_voto: Annotated[str, Field(min_length=64, max_length=64)]
    clave_genetica: Annotated[str, Field(min_length=1)]
    timestamp: Annotated[float, Field(gt=0)]


class AuditoriaVotos(BaseModel):
    """Respuesta del endpoint de auditoria."""

    total: Annotated[int, Field(ge=0)]
    votos_cifrados: list[VotoCifrado]
