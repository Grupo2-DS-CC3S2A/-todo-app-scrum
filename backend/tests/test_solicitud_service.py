"""Tests unitarios para SolicitudService, sumar_dias_habiles y el repositorio."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from src.excepciones.errors import SolicitudDuplicadaError, SolicitudNoEncontradaError
from src.modelos.solicitud import Dependencia, DerivacionInput, EstadoSolicitud, Solicitud
from src.repositorios.solicitud_repo import RepositorioSolicitudEnMemoria
from src.servicios.solicitud_service import (
    DIAS_HABILES_RESPUESTA,
    SolicitudService,
    sumar_dias_habiles,
)


def _payload(**kwargs) -> DerivacionInput:
    defaults = {
        "usuario_id": "usr-001",
        "detalle_solicitud": "Solicitud de prueba con suficiente detalle",
        "dependencia_asignada": Dependencia.MESA_DE_PARTES,
    }
    defaults.update(kwargs)
    return DerivacionInput(**defaults)


class TestSumarDiasHabiles:
    def test_suma_dias_saltando_fin_de_semana(self):
        # Lunes 2026-06-08 + 5 días hábiles = Lunes 2026-06-15
        lunes = date(2026, 6, 8)
        resultado = sumar_dias_habiles(lunes, 5)
        assert resultado == date(2026, 6, 15)

    def test_cero_dias_devuelve_misma_fecha(self):
        inicio = date(2026, 6, 8)
        assert sumar_dias_habiles(inicio, 0) == inicio

    def test_treinta_dias_habiles_supera_seis_semanas(self):
        inicio = date(2026, 6, 8)
        resultado = sumar_dias_habiles(inicio, 30)
        diferencia = (resultado - inicio).days
        assert diferencia >= 30

    def test_dias_negativos_lanza_excepcion(self):
        with pytest.raises(ValueError):
            sumar_dias_habiles(date(2026, 6, 8), -1)


class TestSolicitudService:
    def test_derivar_crea_solicitud_pendiente(self, solicitud_service: SolicitudService):
        s = solicitud_service.derivar(_payload())
        assert s.estado == EstadoSolicitud.PENDIENTE

    def test_derivar_asigna_dependencia_correcta(self, solicitud_service: SolicitudService):
        s = solicitud_service.derivar(_payload(dependencia_asignada=Dependencia.ASESORIA_LEGAL))
        assert s.dependencia_asignada == Dependencia.ASESORIA_LEGAL

    def test_derivar_calcula_fecha_maxima_30_dias_habiles(
        self, solicitud_service: SolicitudService
    ):
        s = solicitud_service.derivar(_payload())
        diferencia = (s.fecha_maxima_respuesta.date() - s.fecha_ingreso.date()).days
        assert diferencia >= DIAS_HABILES_RESPUESTA

    def test_derivar_genera_id_unico(self, solicitud_service: SolicitudService):
        s1 = solicitud_service.derivar(_payload())
        s2 = solicitud_service.derivar(_payload())
        assert s1.id != s2.id

    def test_obtener_solicitud_existente(self, solicitud_service: SolicitudService):
        creada = solicitud_service.derivar(_payload())
        recuperada = solicitud_service.obtener(creada.id)
        assert recuperada.id == creada.id

    def test_obtener_solicitud_inexistente_lanza_error(
        self, solicitud_service: SolicitudService
    ):
        with pytest.raises(SolicitudNoEncontradaError):
            solicitud_service.obtener("id-que-no-existe")

    def test_listar_refleja_todas_las_solicitudes(self, solicitud_service: SolicitudService):
        solicitud_service.derivar(_payload())
        solicitud_service.derivar(_payload())
        assert len(solicitud_service.listar()) == 2


class TestRepositorioSolicitudEnMemoria:
    def _solicitud_valida(self) -> Solicitud:
        ahora = datetime.now(tz=timezone.utc)
        return Solicitud(
            usuario_id="usr-test",
            detalle_solicitud="Detalle válido suficiente para el test",
            dependencia_asignada=Dependencia.LOGISTICA,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=ahora + timedelta(days=45),
        )

    def test_guardar_y_obtener(self):
        repo = RepositorioSolicitudEnMemoria()
        s = self._solicitud_valida()
        guardada = repo.guardar(s)
        assert repo.obtener_por_id(guardada.id).id == guardada.id

    def test_guardar_duplicado_lanza_error(self):
        repo = RepositorioSolicitudEnMemoria()
        s = self._solicitud_valida()
        repo.guardar(s)
        with pytest.raises(SolicitudDuplicadaError):
            repo.guardar(s)

    def test_obtener_inexistente_lanza_error(self):
        repo = RepositorioSolicitudEnMemoria()
        with pytest.raises(SolicitudNoEncontradaError):
            repo.obtener_por_id("no-existe")

    def test_listar_por_usuario(self):
        repo = RepositorioSolicitudEnMemoria()
        ahora = datetime.now(tz=timezone.utc)
        fmax = ahora + timedelta(days=45)
        s1 = Solicitud(
            usuario_id="u1",
            detalle_solicitud="Detalle suficiente para la solicitud",
            dependencia_asignada=Dependencia.TESORERIA,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=fmax,
        )
        s2 = Solicitud(
            usuario_id="u2",
            detalle_solicitud="Otro detalle suficiente para la solicitud",
            dependencia_asignada=Dependencia.TESORERIA,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=fmax,
        )
        repo.guardar(s1)
        repo.guardar(s2)
        assert len(repo.listar_por_usuario("u1")) == 1

    def test_listar_por_dependencia(self):
        repo = RepositorioSolicitudEnMemoria()
        ahora = datetime.now(tz=timezone.utc)
        fmax = ahora + timedelta(days=45)
        s = Solicitud(
            usuario_id="u1",
            detalle_solicitud="Detalle suficiente para la solicitud",
            dependencia_asignada=Dependencia.SECRETARIA_GENERAL,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=fmax,
        )
        repo.guardar(s)
        assert len(repo.listar_por_dependencia(Dependencia.SECRETARIA_GENERAL)) == 1
        assert len(repo.listar_por_dependencia(Dependencia.LOGISTICA)) == 0

    def test_listar_por_estado(self):
        repo = RepositorioSolicitudEnMemoria()
        ahora = datetime.now(tz=timezone.utc)
        fmax = ahora + timedelta(days=45)
        s = Solicitud(
            usuario_id="u1",
            detalle_solicitud="Detalle suficiente para la solicitud",
            dependencia_asignada=Dependencia.RECURSOS_HUMANOS,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=fmax,
        )
        repo.guardar(s)
        assert len(repo.listar_por_estado(EstadoSolicitud.PENDIENTE)) == 1
        assert len(repo.listar_por_estado(EstadoSolicitud.ATENDIDA)) == 0

    def test_listar_todas(self):
        repo = RepositorioSolicitudEnMemoria()
        ahora = datetime.now(tz=timezone.utc)
        fmax = ahora + timedelta(days=45)
        for _ in range(3):
            s = Solicitud(
                usuario_id="u1",
                detalle_solicitud="Detalle suficiente para la solicitud",
                dependencia_asignada=Dependencia.TRAMITE_DOCUMENTARIO,
                fecha_ingreso=ahora,
                fecha_maxima_respuesta=fmax,
            )
            repo.guardar(s)
        assert repo.contar() == 3
        assert len(repo.listar_todas()) == 3
