"""DTOs del endpoint de sugerencia de dependencia (MDP-10)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.modelos.solicitud import DETALLE_MAX_LENGTH, DETALLE_MIN_LENGTH, Dependencia
from src.modelos.tipo_persona import TipoPersona


class SugerenciaDependenciaInput(BaseModel):
    """Payload para pedir una sugerencia antes de derivar (aun sin dependencia)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tipo_persona: Annotated[
        TipoPersona,
        Field(description="Tipo de persona solicitante (Natural o Juridica)."),
    ]
    detalle_solicitud: Annotated[
        str,
        Field(
            min_length=DETALLE_MIN_LENGTH,
            max_length=DETALLE_MAX_LENGTH,
            description="Descripcion textual del asunto de la solicitud.",
        ),
    ]


class SugerenciaDependenciaResponse(BaseModel):
    """Respuesta con la dependencia sugerida y su puntaje de prioridad."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dependencia: Dependencia
    puntaje: float
