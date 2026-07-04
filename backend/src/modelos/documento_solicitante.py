"""Factory Method para el documento de identidad de la solicitud (MDP-15).

Construye, segun el ``TipoPersona`` elegido por el ciudadano (MDP-06), el
documento de identidad especifico que debe acompanar la solicitud: DNI de
8 digitos para Persona Natural, RUC de 11 digitos para Persona Juridica.

La validacion de formato vive en cada subtipo (Pydantic); ``DocumentoFactory``
solo decide que clase instanciar (patron Creacional: Factory Method), sin
duplicar las reglas de validacion.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.excepciones.errors import DocumentoInvalidoError
from src.modelos.tipo_persona import TipoPersona

DNI_PATTERN: str = r"^\d{8}$"
RUC_PATTERN: str = r"^\d{11}$"


class SolicitudPersonaNatural(BaseModel):
    """Documento de identidad de una solicitud de Persona Natural."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tipo_persona: Literal[TipoPersona.NATURAL] = TipoPersona.NATURAL
    dni: Annotated[
        str,
        Field(pattern=DNI_PATTERN, description="DNI peruano de 8 digitos."),
    ]


class SolicitudPersonaJuridica(BaseModel):
    """Documento de identidad de una solicitud de Persona Juridica."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tipo_persona: Literal[TipoPersona.JURIDICA] = TipoPersona.JURIDICA
    ruc: Annotated[
        str,
        Field(pattern=RUC_PATTERN, description="RUC peruano de 11 digitos."),
    ]


DocumentoSolicitante = Union[SolicitudPersonaNatural, SolicitudPersonaJuridica]


class DocumentoFactory:
    """Factory Method que construye el documento segun el tipo de persona.

    Uso: ``DocumentoFactory.crear(TipoPersona.NATURAL, "40392536")``.
    Lanza ``DocumentoInvalidoError`` (400/422, mapeado por el handler de
    dominio) si el numero no cumple el patron del tipo indicado.
    """

    @staticmethod
    def crear(tipo: TipoPersona, numero_documento: str) -> DocumentoSolicitante:
        try:
            if tipo == TipoPersona.NATURAL:
                return SolicitudPersonaNatural(dni=numero_documento)
            if tipo == TipoPersona.JURIDICA:
                return SolicitudPersonaJuridica(ruc=numero_documento)
        except ValidationError as exc:
            raise DocumentoInvalidoError(
                f"Numero de documento invalido para tipo_persona="
                f"{tipo.value}: {numero_documento!r}."
            ) from exc
        raise DocumentoInvalidoError(f"Tipo de persona no soportado: {tipo!r}")
