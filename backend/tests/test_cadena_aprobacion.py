import pytest
from datetime import datetime, timezone, timedelta
from typing import Any
from src.modelos.solicitud import Solicitud, EstadoSolicitud, Dependencia
from src.servicios.cadena_aprobacion import (
    ValidacionCiudadanoHandler,
    AprobacionLegalHandler,
    DerivacionDependenciaHandler,
    ManejadorAprobacion,
)


# Helper: Manejador Espía para Aislar los Eslabones
class SpyManejador(ManejadorAprobacion):
    """
    Un manejador ficticio que registra si el eslabón anterior le delegó
    correctamente la solicitud. Permite aislar las pruebas.
    """

    def __init__(self) -> None:
        super().__init__()
        self.fue_llamado: bool = False
        self.solicitud_recibida: Solicitud | None = None

    def manejar(self, solicitud: Solicitud) -> Any:
        self.fue_llamado = True
        self.solicitud_recibida = solicitud
        return solicitud


fecha_prueba = datetime.now(tz=timezone.utc)
fecha_in_prueba = datetime.now(tz=timezone.utc)
fecha_max_prueba = fecha_in_prueba + timedelta(days=5)


# Pruebas para ValidacionCiudadanoHandler
def test_validacion_ciudadano_handler_exitoso():
    solicitud = Solicitud(
        usuario_id="ciudadano-123",
        detalle_solicitud="Sustento válido de mi solicitud",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = ValidacionCiudadanoHandler()
    espia = SpyManejador()
    handler.set_siguiente(espia)

    handler.manejar(solicitud)

    assert espia.fue_llamado is True
    assert espia.solicitud_recibida.usuario_id == "ciudadano-123"


def test_validacion_ciudadano_handler_falla_sin_usuario():
    solicitud = Solicitud.model_construct(
        usuario_id="",
        detalle_solicitud="Sustento válido de mi solicitud",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = ValidacionCiudadanoHandler()
    espia = SpyManejador()
    handler.set_siguiente(espia)

    with pytest.raises(
        ValueError, match="El usuario no está correctamente identificado"
    ):
        handler.manejar(solicitud)

    assert espia.fue_llamado is False


# Pruebas para AprobacionLegalHandler
def test_aprobacion_legal_handler_exitoso():
    solicitud = Solicitud.model_construct(
        usuario_id="ciudadano-123",
        detalle_solicitud="Sustento con longitud legal suficiente",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = AprobacionLegalHandler()
    espia = SpyManejador()
    handler.set_siguiente(espia)

    handler.manejar(solicitud)

    assert espia.fue_llamado is True


def test_aprobacion_legal_handler_rechazo_mutacion_estado():
    solicitud = Solicitud.model_construct(
        usuario_id="ciudadano-123",
        detalle_solicitud="Muy corto",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = AprobacionLegalHandler()
    espia = SpyManejador()
    handler.set_siguiente(espia)

    resultado = handler.manejar(solicitud)

    assert resultado.estado == EstadoSolicitud.RECHAZADA_LEGAL
    assert espia.fue_llamado is False


# Pruebas para DerivacionDependenciaHandler
def test_derivacion_dependencia_handler_exitoso():
    solicitud = Solicitud(
        usuario_id="ciudadano-123",
        detalle_solicitud="Sustento válido de mi solicitud",
        dependencia_asignada=Dependencia.MESA_DE_PARTES,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = DerivacionDependenciaHandler()

    resultado = handler.manejar(solicitud)

    assert resultado == solicitud


def test_derivacion_dependencia_handler_falla_sin_dependencia():
    solicitud = Solicitud.model_construct(
        usuario_id="ciudadano-123",
        detalle_solicitud="Sustento válido de mi solicitud",
        dependencia_asignada=None,
        estado=EstadoSolicitud.PENDIENTE,
        fecha_ingreso=fecha_in_prueba,
        fecha_maxima_respuesta=fecha_max_prueba,
    )
    handler = DerivacionDependenciaHandler()

    with pytest.raises(ValueError, match="No se ha especificado una dependencia"):
        handler.manejar(solicitud)
