"""Modelos Pydantic para validacion de ciudadano contra SQLite."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ValidacionCiudadanoInput(BaseModel):
    """Payload requerido para validar el acceso a Mesa de Partes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dni: Annotated[
        str,
        Field(
            min_length=8,
            max_length=8,
            pattern=r"^\d{8}$",
            description="DNI peruano de 8 digitos.",
            examples=["40392536"],
        ),
    ]
    digit: Annotated[
        str,
        Field(
            min_length=1,
            max_length=1,
            pattern=r"^\d$",
            description="Digito de verificacion del DNI.",
            examples=["1"],
        ),
    ]
    date: Annotated[
        str,
        Field(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Fecha de emision del DNI en formato YYYY-MM-DD.",
            examples=["2024-07-25"],
        ),
    ]


class CiudadanoValidado(BaseModel):
    """Ciudadano encontrado en la base de validacion."""

    model_config = ConfigDict(extra="forbid")

    dni: str
    digit: str
    issue_date: str
    firstname: str
    lastname: str


class ValidacionCiudadanoResponse(BaseModel):
    """Respuesta del endpoint de validacion de ingreso."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    dni: str | None = None
    firstname: str | None = None
    lastname: str | None = None
