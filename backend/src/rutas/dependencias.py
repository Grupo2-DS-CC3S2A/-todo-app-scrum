from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from supabase import Client, create_client

from src.config import settings


class DependenciaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    nombre: str
    codigo_interno: str


router = APIRouter(
    prefix="/api/dependencias",
    tags=["dependencias"],
)


@router.get("/", response_model=list[DependenciaResponse])
async def listar_dependencias() -> list[DependenciaResponse]:
    """Lista dependencias desde la tabla public.dependencias en Supabase."""
    try:
        client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )

        response = (
            client.table("dependencias")
            .select("id,nombre,codigo_interno")
            .order("nombre")
            .execute()
        )

        return [
            DependenciaResponse(**cast(dict[str, Any], row)) for row in response.data
        ]

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron listar las dependencias.",
        ) from exc
