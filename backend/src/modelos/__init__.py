"""Modelos Pydantic del dominio."""

from src.modelos.solicitud import (
    Dependencia,
    DerivacionInput,
    EstadoSolicitud,
    Solicitud,
    SolicitudDerivada,
    SolicitudInput,
)
from src.modelos.voto import AuditoriaVotos, VotoCifrado, VotoInput

__all__ = [
    "AuditoriaVotos",
    "Dependencia",
    "DerivacionInput",
    "EstadoSolicitud",
    "Solicitud",
    "SolicitudDerivada",
    "SolicitudInput",
    "VotoCifrado",
    "VotoInput",
]
