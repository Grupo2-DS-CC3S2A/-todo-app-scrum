"""Endpoints HTTP del modulo administrativo de Mesa de Partes (HU04).

Expone la operacion protegida que permite al administrador derivar una
solicitud hacia una dependencia interna. La autenticacion/autorizacion
real se delega a un proveedor central; aqui se modela como una
``Depends`` que valida el rol administrador y deja el endpoint listo
para integrar JWT/OIDC sin tocar la logica de dominio.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status

from src.excepciones.errors import NoAutorizadoError
from src.logging_config import get_logger
from src.modelos.solicitud import (
    DerivacionInput,
    Solicitud,
    SolicitudDerivada,
)
from src.servicios.solicitud_service import (
    SolicitudService,
    get_solicitud_service,
)

logger = get_logger(__name__)

router: APIRouter = APIRouter(
    prefix="/api/admin/solicitudes",
    tags=["admin", "mesa-de-partes"],
)


async def verificar_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> str:
    """Dependencia de autorizacion para el rol administrador.

    Implementacion provisional basada en token de cabecera; debe
    sustituirse por validacion JWT contra el IdP corporativo. Se
    mantiene aislada para que rutas/servicios no conozcan el mecanismo.

    Raises:
        NoAutorizadoError: Si el token no se proporciona o no coincide
            con el secreto compartido administrativo.
    """
    import os

    esperado: str | None = os.getenv("ADMIN_TOKEN")
    if not esperado or x_admin_token != esperado:
        raise NoAutorizadoError(
            "Se requiere un token administrativo valido para esta operacion."
        )
    return x_admin_token


def _a_respuesta(solicitud: Solicitud) -> SolicitudDerivada:
    """Mapea la entidad de dominio al DTO publico del endpoint."""
    return SolicitudDerivada(
        id=solicitud.id,
        usuario_id=solicitud.usuario_id,
        detalle_solicitud=solicitud.detalle_solicitud,
        dependencia_asignada=solicitud.dependencia_asignada,
        fecha_ingreso=solicitud.fecha_ingreso,
        fecha_maxima_respuesta=solicitud.fecha_maxima_respuesta,
        estado=solicitud.estado,
    )


@router.post(
    "/derivar",
    response_model=SolicitudDerivada,
    status_code=status.HTTP_201_CREATED,
    summary="Deriva una solicitud a la dependencia correspondiente.",
)
async def derivar_solicitud(
    payload: DerivacionInput,
    servicio: SolicitudService = Depends(get_solicitud_service),
    _admin: str = Depends(verificar_admin),
) -> SolicitudDerivada:
    """Deriva la solicitud (HU04).

    Calcula automaticamente la ``fecha_ingreso`` (instante actual) y la
    ``fecha_maxima_respuesta`` (30 dias habiles) y deja la solicitud en
    estado ``Pendiente``.
    """
    solicitud: Solicitud = servicio.derivar(payload)
    return _a_respuesta(solicitud)


@router.get(
    "/{solicitud_id}",
    response_model=SolicitudDerivada,
    summary="Consulta el estado de una solicitud derivada.",
)
async def obtener_solicitud(
    solicitud_id: str,
    servicio: SolicitudService = Depends(get_solicitud_service),
    _admin: str = Depends(verificar_admin),
) -> SolicitudDerivada:
    """Devuelve los datos de auditoria de una solicitud por id."""
    solicitud: Solicitud = servicio.obtener(solicitud_id)
    return _a_respuesta(solicitud)
