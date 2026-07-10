from __future__ import annotations

from datetime import date
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from supabase import Client, create_client

from src.config import settings
from src.excepciones.errors import PlazoVencidoError, TramiteNoReemplazableError
from src.repositorios.documento_tramitado_repo import DocumentoTramitadoRepository


class TramiteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dni: str = Field(..., min_length=8, max_length=8)
    tipo_documento: str
    dependencia: str
    contenedor: str


class TramiteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    dni: str
    nro_documento: str
    tipo_documento: str
    dependencia: str
    estado_documento: str
    fecha_tramite: date
    fecha_respuesta: date
    contenedor: str
    motivo_rechazo: str | None = None
    fecha_resolucion: date | None = None


class TramiteReemplazoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dni: str = Field(..., min_length=8, max_length=8)
    contenedor: str


router = APIRouter(
    prefix="/api/tramites",
    tags=["tramites"],
)


def get_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
    )


@router.post("/", response_model=TramiteResponse, status_code=status.HTTP_201_CREATED)
async def registrar_tramite(payload: TramiteCreateRequest) -> TramiteResponse:
    tipo_documento = payload.tipo_documento.upper().strip()

    if tipo_documento not in {"CARTA", "SOLICITUD", "OFICIO"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de documento no válido.",
        )

    try:
        client = get_client()

        data = {
            "dni": payload.dni,
            "tipo_documento": tipo_documento,
            "dependencia": payload.dependencia,
            "contenedor": payload.contenedor,
        }

        response = (
            client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .insert(data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo registrar el trámite.",
            )

        return TramiteResponse(**cast(dict[str, Any], response.data[0]))

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar el trámite.",
        ) from exc


@router.get("/{dni}", response_model=list[TramiteResponse])
async def listar_tramites_por_dni(dni: str) -> list[TramiteResponse]:
    try:
        client = get_client()

        response = (
            client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .select("*")
            .eq("dni", dni)
            .order("fecha_tramite", desc=True)
            .order("created_at", desc=True)
            .execute()
        )

        return [TramiteResponse(**cast(dict[str, Any], row)) for row in response.data]

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron listar los trámites.",
        ) from exc


@router.get("/{dni}/buscar", response_model=list[TramiteResponse])
async def buscar_tramites(
    dni: str,
    tipo_documento: str = Query(...),
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
) -> list[TramiteResponse]:
    if fecha_hasta < fecha_desde:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La Fecha Hasta debe ser mayor o igual a la Fecha Desde.",
        )

    tipo_documento = tipo_documento.upper().strip()

    if tipo_documento not in {"CARTA", "SOLICITUD", "OFICIO"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de documento no válido.",
        )

    try:
        client = get_client()

        response = (
            client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .select("*")
            .eq("dni", dni)
            .eq("tipo_documento", tipo_documento)
            .gte("fecha_tramite", fecha_desde.isoformat())
            .lte("fecha_tramite", fecha_hasta.isoformat())
            .order("fecha_tramite", desc=True)
            .order("created_at", desc=True)
            .execute()
        )

        return [TramiteResponse(**cast(dict[str, Any], row)) for row in response.data]

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo realizar la búsqueda de trámites.",
        ) from exc


@router.patch("/{tramite_id}/reemplazo", response_model=TramiteResponse)
async def reemplazar_tramite(
    tramite_id: int, payload: TramiteReemplazoRequest
) -> TramiteResponse:
    repository = DocumentoTramitadoRepository(get_client())

    documento = repository.obtener_por_id(tramite_id)
    if documento is None or documento.get("dni") != payload.dni:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe el trámite indicado para ese DNI.",
        )

    if documento["estado_documento"] != "RECHAZADO":
        raise TramiteNoReemplazableError(
            "Solo se puede reemplazar un documento en estado RECHAZADO."
        )

    fecha_respuesta = date.fromisoformat(str(documento["fecha_respuesta"]))
    if date.today() > fecha_respuesta:
        raise PlazoVencidoError("El plazo para reemplazar este documento ya venció.")

    actualizado = repository.actualizar_reemplazo(tramite_id, payload.contenedor)
    if actualizado is None:
        raise TramiteNoReemplazableError(
            "El documento ya no está disponible para reemplazo."
        )

    return TramiteResponse(**actualizado)
