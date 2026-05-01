"""Endpoints HTTP del modulo de votacion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.logging_config import get_logger
from src.modelos.voto import AuditoriaVotos, VotoCifrado, VotoInput
from src.servicios.voto_service import VotoService, get_voto_service

logger = get_logger(__name__)

router: APIRouter = APIRouter(prefix="/api", tags=["votacion"])


@router.post(
    "/votar",
    response_model=VotoCifrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un voto cifrado y devuelve el comprobante.",
)
async def registrar_voto(
    voto: VotoInput,
    servicio: VotoService = Depends(get_voto_service),
) -> VotoCifrado:
    """Registra un voto aplicando llave evolutiva + hash SHA-256.

    Args:
        voto: Payload validado del voto entrante.
        servicio: Servicio de dominio inyectado por FastAPI.

    Returns:
        Comprobante anonimo (``VotoCifrado``) del voto registrado.

    Raises:
        HTTPException: 500 si ocurre un error interno inesperado.
    """
    try:
        return servicio.registrar_voto(voto)
    except ValueError as exc:
        logger.warning("Voto rechazado por validacion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/votos_audit",
    response_model=AuditoriaVotos,
    summary="Devuelve los votos cifrados para auditoria.",
)
async def auditar_votos(
    servicio: VotoService = Depends(get_voto_service),
) -> AuditoriaVotos:
    """Devuelve la lista anonima de comprobantes para auditoria."""
    votos: list[VotoCifrado] = servicio.listar_votos()
    return AuditoriaVotos(total=len(votos), votos_cifrados=votos)
