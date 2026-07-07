"""Tests del Decorator de auditoria sobre ``SolicitudRepository``."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest

from src.excepciones.errors import SolicitudDuplicadaError
from src.modelos.solicitud import Dependencia, EstadoSolicitud, Solicitud
from src.repositorios.solicitud_repo import RepositorioSolicitudEnMemoria
from src.repositorios.solicitud_repo_auditoria import (
    RepositorioSolicitudConAuditoria,
)


def _solicitud(usuario_id: str = "usuario-01") -> Solicitud:
    ahora = datetime.now(tz=timezone.utc)
    return Solicitud(
        usuario_id=usuario_id,
        detalle_solicitud="Solicito constancia de tramite documentario.",
        dependencia_asignada=Dependencia.TRAMITE_DOCUMENTARIO,
        fecha_ingreso=ahora,
        fecha_maxima_respuesta=ahora + timedelta(days=30),
        estado=EstadoSolicitud.PENDIENTE,
    )


@pytest.fixture
def repo_auditado() -> RepositorioSolicitudConAuditoria:
    return RepositorioSolicitudConAuditoria(RepositorioSolicitudEnMemoria())


def test_guardar_delega_y_registra_auditoria(
    repo_auditado: RepositorioSolicitudConAuditoria,
    caplog: pytest.LogCaptureFixture,
) -> None:
    solicitud = _solicitud()
    with caplog.at_level(logging.INFO):
        resultado = repo_auditado.guardar(solicitud)

    assert resultado == solicitud
    assert repo_auditado.obtener_por_id(solicitud.id) == solicitud
    assert "AUDITORIA guardar" in caplog.text
    assert solicitud.id in caplog.text


def test_duplicado_propaga_error_del_componente_envuelto(
    repo_auditado: RepositorioSolicitudConAuditoria,
) -> None:
    solicitud = _solicitud()
    repo_auditado.guardar(solicitud)
    with pytest.raises(SolicitudDuplicadaError):
        repo_auditado.guardar(solicitud)


def test_lecturas_delegan_sin_alterar_resultados(
    repo_auditado: RepositorioSolicitudConAuditoria,
) -> None:
    s1 = _solicitud("usuario-01")
    s2 = _solicitud("usuario-02")
    repo_auditado.guardar(s1)
    repo_auditado.guardar(s2)

    assert repo_auditado.contar() == 2
    assert set(s.id for s in repo_auditado.listar_todas()) == {s1.id, s2.id}
    assert repo_auditado.listar_por_usuario("usuario-01") == [s1]
    assert (
        repo_auditado.listar_por_dependencia(Dependencia.TRAMITE_DOCUMENTARIO)
        == repo_auditado.listar_todas()
    )
    assert repo_auditado.listar_por_estado(EstadoSolicitud.PENDIENTE) != []
