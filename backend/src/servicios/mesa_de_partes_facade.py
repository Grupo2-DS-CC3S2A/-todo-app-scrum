"""Facade (Estructural) del subsistema Mesa de Partes.

Punto de entrada unico para la capa HTTP administrativa: detras de esta
fachada viven la sugerencia de dependencia (Strategy, MDP-10), la
derivacion con su cadena de aprobacion (Chain of Responsibility, MDP-07),
la validacion del documento (Factory Method, MDP-15), la persistencia
(Repository) y la notificacion al ciudadano (Bridge).

Antes de la fachada cada ruta importaba y coordinaba varios servicios por
su cuenta; ahora las rutas dependen de UNA sola abstraccion y el orden de
orquestacion vive en un unico lugar.
"""

from __future__ import annotations

from fastapi import Depends

from src.modelos.solicitud import DerivacionInput, EstadoSolicitud, Solicitud
from src.modelos.tipo_persona import TipoPersona
from src.servicios.enrutamiento_service import (
    SugerenciaDependencia,
    SugerenciaDependenciaService,
    get_sugerencia_dependencia_service,
)
from src.servicios.notificaciones import (
    CanalConsola,
    CanalNotificacion,
    NotificacionDerivacion,
    NotificacionRechazoLegal,
)
from src.servicios.solicitud_service import (
    SolicitudService,
    get_solicitud_service,
)


class MesaDePartesFacade:
    """Orquesta el ciclo administrativo completo de una solicitud.

    Expone las cuatro operaciones que la capa HTTP necesita (sugerir,
    derivar, obtener, listar) y esconde la coordinacion entre servicios.
    Tras derivar, dispara la notificacion adecuada segun el estado final
    (Bridge: el tipo de notificacion y el canal varian por separado).
    """

    def __init__(
        self,
        solicitudes: SolicitudService,
        sugerencias: SugerenciaDependenciaService,
        canal_notificacion: CanalNotificacion | None = None,
    ) -> None:
        self._solicitudes = solicitudes
        self._sugerencias = sugerencias
        self._canal = canal_notificacion or CanalConsola()

    def sugerir(
        self, tipo_persona: TipoPersona, detalle_solicitud: str
    ) -> SugerenciaDependencia:
        """Sugiere dependencia y puntaje sin persistir nada (MDP-10)."""
        return self._sugerencias.sugerir(tipo_persona, detalle_solicitud)

    def derivar(self, payload: DerivacionInput) -> Solicitud:
        """Deriva la solicitud y notifica el resultado al ciudadano."""
        solicitud = self._solicitudes.derivar(payload)
        self._notificar(solicitud)
        return solicitud

    def obtener(self, solicitud_id: str) -> Solicitud:
        """Recupera una solicitud por id."""
        return self._solicitudes.obtener(solicitud_id)

    def listar(self) -> list[Solicitud]:
        """Devuelve todas las solicitudes almacenadas."""
        return self._solicitudes.listar()

    def _notificar(self, solicitud: Solicitud) -> None:
        if solicitud.estado is EstadoSolicitud.RECHAZADA_LEGAL:
            NotificacionRechazoLegal(self._canal).notificar(solicitud)
        else:
            NotificacionDerivacion(self._canal).notificar(solicitud)


def get_mesa_de_partes_facade(
    solicitudes: SolicitudService = Depends(get_solicitud_service),
    sugerencias: SugerenciaDependenciaService = Depends(
        get_sugerencia_dependencia_service
    ),
) -> MesaDePartesFacade:
    """Provee la fachada resolviendo sus servicios via FastAPI ``Depends``.

    Al declarar los servicios como sub-dependencias, los overrides de
    tests (``app.dependency_overrides[get_solicitud_service]``) siguen
    aplicando sin cambios: la fachada recibe el servicio ya resuelto.
    """
    return MesaDePartesFacade(solicitudes=solicitudes, sugerencias=sugerencias)


__all__ = ["MesaDePartesFacade", "get_mesa_de_partes_facade"]
