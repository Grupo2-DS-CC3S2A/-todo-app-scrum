"""Tests del Bridge de notificaciones (tipos x canales independientes)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest

from src.modelos.solicitud import Dependencia, EstadoSolicitud, Solicitud
from src.servicios.notificaciones import (
    CanalConsola,
    CanalEmail,
    CanalNotificacion,
    CanalSMS,
    NotificacionDerivacion,
    NotificacionRechazoLegal,
)


class CanalEspia(CanalNotificacion):
    """Canal falso que captura los envios para inspeccionarlos."""

    def __init__(self) -> None:
        self.envios: list[tuple[str, str, str]] = []

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        self.envios.append((destinatario, asunto, cuerpo))


def _solicitud(estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE) -> Solicitud:
    ahora = datetime.now(tz=timezone.utc)
    return Solicitud(
        usuario_id="usuario-01",
        detalle_solicitud="Solicito copia certificada de mi acta.",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        fecha_ingreso=ahora,
        fecha_maxima_respuesta=ahora + timedelta(days=30),
        estado=estado,
    )


def test_notificacion_derivacion_compone_asunto_y_cuerpo() -> None:
    canal = CanalEspia()
    solicitud = _solicitud()

    NotificacionDerivacion(canal).notificar(solicitud)

    assert len(canal.envios) == 1
    destinatario, asunto, cuerpo = canal.envios[0]
    assert destinatario == solicitud.usuario_id
    assert solicitud.id in asunto
    assert "derivada" in asunto
    assert Dependencia.MESA_DE_PARTES.value in cuerpo
    assert solicitud.fecha_maxima_respuesta.date().isoformat() in cuerpo


def test_notificacion_rechazo_legal_compone_mensaje_de_rechazo() -> None:
    canal = CanalEspia()
    solicitud = _solicitud(estado=EstadoSolicitud.RECHAZADA_LEGAL)

    NotificacionRechazoLegal(canal).notificar(solicitud)

    _, asunto, cuerpo = canal.envios[0]
    assert "rechazada" in asunto
    assert "Asesoria Legal" in cuerpo


def test_mismo_notificador_funciona_con_cualquier_canal(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Esencia del Bridge: la abstraccion no cambia al variar el canal."""
    solicitud = _solicitud()
    with caplog.at_level(logging.INFO):
        NotificacionDerivacion(CanalConsola()).notificar(solicitud)
        NotificacionDerivacion(CanalEmail()).notificar(solicitud)
        NotificacionDerivacion(CanalSMS()).notificar(solicitud)

    assert "NOTIFICACION" in caplog.text
    assert "EMAIL (stub)" in caplog.text
    assert "SMS (stub)" in caplog.text
    assert caplog.text.count(solicitud.usuario_id) >= 3
