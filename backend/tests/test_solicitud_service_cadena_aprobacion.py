"""Test de integración: SolicitudService.derivar() debe persistir 
el resultado real de la cadena de aprobación, no el original.
"""

from __future__ import annotations

import pytest

from src.modelos.solicitud import Dependencia, DerivacionInput, EstadoSolicitud
from src.modelos.tipo_persona import TipoPersona
from src.servicios.solicitud_service import SolicitudService


def _payload_detalle_corto(detalle_solicitud: str) -> DerivacionInput:
    return DerivacionInput(
        usuario_id="usr-001",
        detalle_solicitud=detalle_solicitud,
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        tipo_persona=TipoPersona.NATURAL,
        numero_documento="40392536",
    )


class TestDerivarPersisteResultadoDeLaCadena:
    def test_detalle_menor_a_15_caracteres_persiste_rechazada_legal(
        self, solicitud_service: SolicitudService
    ):
        # 11 caracteres pasa la validacion de Pydantic (minimo 10)
        # pero se rechaza por AprobacionLegalHandler (minimo 15).
        s = solicitud_service.derivar(_payload_detalle_corto("Muy corto12"))
        assert s.estado == EstadoSolicitud.RECHAZADA_LEGAL

    def test_solicitud_rechazada_legalmente_queda_persistida_con_ese_estado(
        self, solicitud_service: SolicitudService
    ):
        creada = solicitud_service.derivar(_payload_detalle_corto("Muy corto12"))
        recuperada = solicitud_service.obtener(creada.id)
        assert recuperada.estado == EstadoSolicitud.RECHAZADA_LEGAL

    @pytest.mark.parametrize(
        "detalle_valido",
        [
            "Solicitud con detalle suficientemente largo",
            "Otro detalle válido con más de quince caracteres",
        ],
    )
    def test_detalle_de_15_caracteres_o_mas_no_se_rechaza(
        self, solicitud_service: SolicitudService, detalle_valido: str
    ):
        s = solicitud_service.derivar(_payload_detalle_corto(detalle_valido))
        assert s.estado == EstadoSolicitud.PENDIENTE
