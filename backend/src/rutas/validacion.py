"""Endpoints de validacion de ingreso para Mesa de Partes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.logging_config import get_logger
from src.modelos.ciudadano import (
    ValidacionCiudadanoInput,
    ValidacionCiudadanoResponse,
)
from src.servicios.ciudadano_service import CiudadanoService, get_ciudadano_service

logger = get_logger(__name__)

router: APIRouter = APIRouter(tags=["validacion-ciudadano"])


@router.post(
    "/api/validate",
    response_model=ValidacionCiudadanoResponse,
    summary="Valida DNI, digito y fecha de emision contra validation.db.",
)
async def validar_ciudadano_api(
    payload: ValidacionCiudadanoInput,
    servicio: CiudadanoService = Depends(get_ciudadano_service),
) -> ValidacionCiudadanoResponse:
    """Endpoint usado por el frontend React integrado."""
    try:
        respuesta = servicio.validar(payload)
        logger.info(
            "Validacion ciudadano | dni=%s | valid=%s",
            payload.dni,
            respuesta.valid,
        )
        return respuesta
    except FileNotFoundError as exc:
        logger.exception("Base de validacion no encontrada.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/validate",
    response_model=ValidacionCiudadanoResponse,
    summary="Endpoint compatible con el prototipo HTML original.",
)
async def validar_ciudadano_legacy(
    payload: ValidacionCiudadanoInput,
    servicio: CiudadanoService = Depends(get_ciudadano_service),
) -> ValidacionCiudadanoResponse:
    """Mantiene compatibilidad con MesaParteReniec original."""
    return await validar_ciudadano_api(payload, servicio)
