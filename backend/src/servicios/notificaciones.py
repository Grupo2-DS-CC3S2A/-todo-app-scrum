"""Bridge (Estructural) para notificaciones al ciudadano.

Separa la jerarquia de *que* se notifica (``NotificadorSolicitud`` y sus
refinamientos: derivacion exitosa, rechazo legal) de la jerarquia de *como*
se envia (``CanalNotificacion``: consola/log, email, SMS). Ambas dimensiones
varian de forma independiente: agregar un canal nuevo no toca los tipos de
notificacion y viceversa — sin Bridge, N tipos x M canales explotarian en
N*M subclases.

Los canales Email y SMS son stubs deliberados: registran el envio con el
formato final del mensaje pero no integran un proveedor externo todavia
(el formulario del frontend ya captura correo y celular; la integracion
SMTP/SMS es un paso posterior que solo requiere reemplazar el canal).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.logging_config import get_logger
from src.modelos.solicitud import Solicitud

logger = get_logger(__name__)


class CanalNotificacion(ABC):
    """Implementador del Bridge: mecanismo concreto de envio."""

    @abstractmethod
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        """Envia el mensaje al destinatario por el medio concreto."""


class CanalConsola(CanalNotificacion):
    """Canal de desarrollo/demo: escribe la notificacion en el log."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        logger.info(
            "NOTIFICACION | destinatario=%s | asunto=%s | %s",
            destinatario,
            asunto,
            cuerpo,
        )


class CanalEmail(CanalNotificacion):
    """Canal de correo electronico (stub: pendiente integracion SMTP)."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        logger.info(
            "EMAIL (stub) | para=%s | asunto=%s | %s",
            destinatario,
            asunto,
            cuerpo,
        )


class CanalSMS(CanalNotificacion):
    """Canal SMS (stub: pendiente integracion con proveedor)."""

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        logger.info(
            "SMS (stub) | para=%s | asunto=%s | %s",
            destinatario,
            asunto,
            cuerpo,
        )


class NotificadorSolicitud(ABC):
    """Abstraccion del Bridge: notificacion sobre el ciclo de vida.

    Mantiene la referencia al canal (puente) y delega en el la entrega;
    las subclases solo deciden asunto y cuerpo del mensaje.
    """

    def __init__(self, canal: CanalNotificacion) -> None:
        self._canal = canal

    @abstractmethod
    def _componer(self, solicitud: Solicitud) -> tuple[str, str]:
        """Devuelve ``(asunto, cuerpo)`` para la solicitud dada."""

    def notificar(self, solicitud: Solicitud) -> None:
        """Compone el mensaje y lo entrega por el canal configurado."""
        asunto, cuerpo = self._componer(solicitud)
        self._canal.enviar(solicitud.usuario_id, asunto, cuerpo)


class NotificacionDerivacion(NotificadorSolicitud):
    """Notifica que la solicitud fue derivada a una dependencia."""

    def _componer(self, solicitud: Solicitud) -> tuple[str, str]:
        asunto = f"Solicitud {solicitud.id} derivada"
        cuerpo = (
            f"Su solicitud fue derivada a "
            f"{solicitud.dependencia_asignada.value} en estado "
            f"{solicitud.estado.value}. Fecha maxima de respuesta: "
            f"{solicitud.fecha_maxima_respuesta.date().isoformat()}."
        )
        return asunto, cuerpo


class NotificacionRechazoLegal(NotificadorSolicitud):
    """Notifica que Asesoria Legal rechazo la solicitud."""

    def _componer(self, solicitud: Solicitud) -> tuple[str, str]:
        asunto = f"Solicitud {solicitud.id} rechazada"
        cuerpo = (
            "Su solicitud fue rechazada por Asesoria Legal: el detalle "
            "no cumple los requisitos minimos. Puede corregirla y "
            "presentarla nuevamente."
        )
        return asunto, cuerpo


__all__ = [
    "CanalNotificacion",
    "CanalConsola",
    "CanalEmail",
    "CanalSMS",
    "NotificadorSolicitud",
    "NotificacionDerivacion",
    "NotificacionRechazoLegal",
]
