"""Endpoints HTTP del modulo administrativo de Mesa de Partes (HU04).

Expone la operacion protegida que permite al administrador derivar una
solicitud hacia una dependencia interna. La autenticacion/autorizacion
real se delega a un proveedor central; aqui se modela como una
``Depends`` que valida el rol administrador y deja el endpoint listo
para integrar JWT/OIDC sin tocar la logica de dominio.

Las rutas dependen unicamente de ``MesaDePartesFacade`` (Facade): la
coordinacion entre derivacion, sugerencia y notificacion vive detras de
esa unica abstraccion, no aqui.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.excepciones.errors import NoAutorizadoError
from src.logging_config import get_logger
from src.modelos.solicitud import (
    DerivacionInput,
    Solicitud,
    SolicitudDerivada,
)
from src.modelos.sugerencia import (
    SugerenciaDependenciaInput,
    SugerenciaDependenciaResponse,
)
from src.modelos.usuario import RolUsuario
from src.servicios.auth_service import AuthService, get_auth_service
from src.servicios.mesa_de_partes_facade import (
    MesaDePartesFacade,
    get_mesa_de_partes_facade,
)

_bearer_scheme = HTTPBearer(auto_error=False)

logger = get_logger(__name__)

router: APIRouter = APIRouter(
    prefix="/api/admin/solicitudes",
    tags=["admin", "mesa-de-partes"],
)


async def verificar_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth: AuthService = Depends(get_auth_service),
) -> str:
    """Dependencia de autorizacion para el rol administrador.

    Acepta dos esquemas (en este orden):

    1. JWT Bearer (S2-05): ``Authorization: Bearer <token>`` con claim
       ``rol == "admin"``. Es el mecanismo recomendado.
    2. ``X-Admin-Token`` legacy: token secreto compartido configurable via
       variable de entorno ``ADMIN_TOKEN``. Se mantiene por compatibilidad
       con tests y clientes existentes; se removera tras S2-06.
    """
    if credentials is not None and credentials.credentials:
        try:
            payload = auth.decodificar_token(credentials.credentials)
        except Exception as exc:
            raise NoAutorizadoError("Token JWT invalido o expirado.") from exc
        if payload.get("rol") != RolUsuario.ADMIN.value:
            raise NoAutorizadoError(
                "El usuario autenticado no tiene rol administrador."
            )
        return payload.get("sub", "")

    esperado = os.getenv("ADMIN_TOKEN", "RENIEC_ADMIN_SUPER_SECRET_2026")
    if not x_admin_token or x_admin_token != esperado:
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
        tipo_persona=solicitud.tipo_persona,
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
    fachada: MesaDePartesFacade = Depends(get_mesa_de_partes_facade),
    _admin: str = Depends(verificar_admin),
) -> SolicitudDerivada:
    """Deriva la solicitud (HU04).

    Calcula automaticamente la ``fecha_ingreso`` (instante actual) y la
    ``fecha_maxima_respuesta`` (30 dias habiles) y deja la solicitud en
    estado ``Pendiente``.
    """
    solicitud: Solicitud = fachada.derivar(payload)
    return _a_respuesta(solicitud)


@router.post(
    "/sugerir-dependencia",
    response_model=SugerenciaDependenciaResponse,
    summary="Sugiere una dependencia y un puntaje de prioridad (MDP-10).",
)
async def sugerir_dependencia(
    payload: SugerenciaDependenciaInput,
    fachada: MesaDePartesFacade = Depends(get_mesa_de_partes_facade),
    _admin: str = Depends(verificar_admin),
) -> SugerenciaDependenciaResponse:
    """Sugiere dependencia y prioridad antes de derivar (Strategy, MDP-10).

    El admin puede aceptar la sugerencia o sobreescribirla al derivar:
    este endpoint no persiste nada, solo calcula la recomendacion.
    """
    sugerencia = fachada.sugerir(payload.tipo_persona, payload.detalle_solicitud)
    return SugerenciaDependenciaResponse(
        dependencia=sugerencia.dependencia,
        puntaje=sugerencia.puntaje,
    )


@router.get(
    "/{solicitud_id}",
    response_model=SolicitudDerivada,
    summary="Consulta el estado de una solicitud derivada.",
)
async def obtener_solicitud(
    solicitud_id: str,
    fachada: MesaDePartesFacade = Depends(get_mesa_de_partes_facade),
    _admin: str = Depends(verificar_admin),
) -> SolicitudDerivada:
    """Devuelve los datos de auditoria de una solicitud por id."""
    solicitud: Solicitud = fachada.obtener(solicitud_id)
    return _a_respuesta(solicitud)


@router.get(
    "/",
    response_model=list[Solicitud],
    summary="Listar todas las solicitudes del sistema.",
)
async def listar_todas(
    fachada: MesaDePartesFacade = Depends(get_mesa_de_partes_facade),
    _admin: str = Depends(verificar_admin),
) -> list[Solicitud]:
    """Retorna el listado completo de solicitudes para auditoria o gestion admin."""
    return fachada.listar()
