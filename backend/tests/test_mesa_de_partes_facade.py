"""Tests del Facade del subsistema Mesa de Partes."""

from __future__ import annotations

from src.modelos.solicitud import (
    Dependencia,
    DerivacionInput,
    EstadoSolicitud,
)
from src.modelos.tipo_persona import TipoPersona
from src.servicios.enrutamiento_service import (
    EnrutamientoReglas,
    SugerenciaDependenciaService,
)
from src.servicios.mesa_de_partes_facade import MesaDePartesFacade
from src.servicios.notificaciones import CanalNotificacion
from src.servicios.solicitud_service import SolicitudService


class CanalEspia(CanalNotificacion):
    def __init__(self) -> None:
        self.envios: list[tuple[str, str, str]] = []

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        self.envios.append((destinatario, asunto, cuerpo))


def _fachada(canal: CanalNotificacion) -> MesaDePartesFacade:
    return MesaDePartesFacade(
        solicitudes=SolicitudService(),
        sugerencias=SugerenciaDependenciaService(estrategia=EnrutamientoReglas()),
        canal_notificacion=canal,
    )


def _payload(detalle: str) -> DerivacionInput:
    return DerivacionInput(
        usuario_id="usuario-01",
        detalle_solicitud=detalle,
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        tipo_persona=TipoPersona.NATURAL,
        numero_documento="40392536",
    )


def test_derivar_persiste_y_notifica_derivacion() -> None:
    canal = CanalEspia()
    fachada = _fachada(canal)

    solicitud = fachada.derivar(
        _payload("Solicito copia certificada de mi acta de nacimiento.")
    )

    assert solicitud.estado is EstadoSolicitud.PENDIENTE
    assert fachada.obtener(solicitud.id).id == solicitud.id
    assert len(canal.envios) == 1
    _, asunto, _ = canal.envios[0]
    assert "derivada" in asunto


def test_derivar_rechazada_legal_notifica_rechazo() -> None:
    canal = CanalEspia()
    fachada = _fachada(canal)

    # 10-14 caracteres: pasa el minimo del modelo (10) pero no el umbral
    # legal de la cadena de aprobacion (15) -> RECHAZADA_LEGAL.
    solicitud = fachada.derivar(_payload("corto legal"))

    assert solicitud.estado is EstadoSolicitud.RECHAZADA_LEGAL
    _, asunto, cuerpo = canal.envios[0]
    assert "rechazada" in asunto
    assert "Asesoria Legal" in cuerpo


def test_sugerir_delega_en_la_estrategia_configurada() -> None:
    fachada = _fachada(CanalEspia())

    sugerencia = fachada.sugerir(
        TipoPersona.NATURAL, "Consulta sobre rectificacion de datos."
    )

    assert sugerencia.dependencia is Dependencia.MESA_DE_PARTES
    assert sugerencia.puntaje == 50.0  # heuristica determinista de reglas


def test_listar_expone_todo_el_subsistema() -> None:
    fachada = _fachada(CanalEspia())
    fachada.derivar(_payload("Primera solicitud valida del ciudadano."))
    fachada.derivar(_payload("Segunda solicitud valida del ciudadano."))

    assert len(fachada.listar()) == 2
