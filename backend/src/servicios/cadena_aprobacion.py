from abc import ABC, abstractmethod
from typing import Optional, Any

# Importamos el modelo de la solicitud
from src.modelos.solicitud import Solicitud, EstadoSolicitud


class ManejadorAprobacion(ABC):
    """
    Clase base para la Cadena de Responsabilidades
    Declara el método para construir la cadena y el método para ejecutarla.
    """

    def __init__(self) -> None:
        # Almacena la referencia al siguiente eslabon de la cadena
        self._siguiente_manejador: Optional["ManejadorAprobacion"] = None

    def set_siguiente(self, manejador: "ManejadorAprobacion") -> "ManejadorAprobacion":
        """
        Define el siguiente manejador en la cadena.

        Retorna el manejador recibido para permitir el encadenamiento fluido.
        """
        self._siguiente_manejador = manejador
        return manejador

    @abstractmethod
    def manejar(self, solicitud: Solicitud) -> Any:
        """
        Procesa la solicitud.
        Si la clase hija no puede procesarla por completo o si necesita
        continuar el flujo, debe llamar a `super().manejar(solicitud)`.
        """
        if self._siguiente_manejador is not None:
            return self._siguiente_manejador.manejar(solicitud)

        # Si llegamos al final de la cadena sin ser manejada/rechazada
        return None


class ValidacionCiudadanoHandler(ManejadorAprobacion):
    """
    Primer eslabón: Verifica que el ciudadano cumpla con los requisitos
    para emitir la solicitud (ej. identidad validada, sin deudas, etc.).
    """

    def manejar(self, solicitud: Solicitud) -> Any:
        if not solicitud.usuario_id:
            raise ValueError(
                "Rechazado: El usuario no está correctamente identificado."
            )

        # Si todo es correcto, pasa la solicitud al siguiente eslabón
        return super().manejar(solicitud)


class AprobacionLegalHandler(ManejadorAprobacion):
    """
    Segundo eslabón: Verifica que el contenido de la solicitud
    cumpla con el marco legal o los requisitos mínimos de forma.
    """


def manejar(self, solicitud: Solicitud) -> Any:
    if not solicitud.detalle_solicitud or len(solicitud.detalle_solicitud) < 15:

        solicitud.estado = EstadoSolicitud.RECHAZADA_LEGAL

        # Rompemos la cadena: retornamos la solicitud directamente sin pasársela al DerivacionDependenciaHandler
        return solicitud

    # Si la validación es exitosa, pasa la solicitud al siguiente eslabón
    return super().manejar(solicitud)


class DerivacionDependenciaHandler(ManejadorAprobacion):
    """
    Tercer y último eslabón: Se encarga de asignar la dependencia
    y dar el visto bueno final al flujo.
    """

    def manejar(self, solicitud: Solicitud) -> Any:
        # Ultimo paso, se aprobo al ciudadano y la legalidad

        if not solicitud.dependencia_asignada:
            raise ValueError(
                "Error: No se ha especificado una dependencia para la derivación."
            )

        return solicitud
