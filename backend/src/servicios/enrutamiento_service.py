"""Strategy (Comportamiento) para sugerir dependencia y prioridad (MDP-10).

Reutiliza ``utilidades/algoritmo_genetico.py`` (motor genetico ya existente,
sin modificar) como fuente de variabilidad para el puntaje de prioridad de
``EnrutamientoGenetico``. La eleccion de la dependencia en si es una regla
de negocio (que area corresponde a cada tipo de persona) compartida por
ambas estrategias: lo que las diferencia es como calculan el puntaje, no
la dependencia sugerida — así siguen siendo intercambiables (Strategy) sin
romper el contrato de salida ``SugerenciaDependencia``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

from src.modelos.solicitud import Dependencia
from src.modelos.tipo_persona import TipoPersona
from src.utilidades.algoritmo_genetico import AlgoritmoGenetico, Mutacion

PUNTAJE_MIN: float = 0.0
PUNTAJE_MAX: float = 100.0

_DEPENDENCIA_POR_TIPO: dict[TipoPersona, Dependencia] = {
    TipoPersona.NATURAL: Dependencia.MESA_DE_PARTES,
    TipoPersona.JURIDICA: Dependencia.ASESORIA_LEGAL,
}


def _dependencia_por_tipo(tipo_persona: TipoPersona) -> Dependencia:
    """Regla de negocio: dependencia base segun tipo de persona."""
    return _DEPENDENCIA_POR_TIPO[tipo_persona]


@dataclass(frozen=True, slots=True)
class SugerenciaDependencia:
    """Resultado de una estrategia de enrutamiento."""

    dependencia: Dependencia
    puntaje: float


class EstrategiaEnrutamiento(ABC):
    """Interfaz Strategy: sugiere dependencia y puntaje de prioridad."""

    @abstractmethod
    def sugerir(
        self, tipo_persona: TipoPersona, detalle_solicitud: str
    ) -> SugerenciaDependencia:
        """Sugiere una dependencia y un puntaje de prioridad en [0, 100]."""
        raise NotImplementedError


class EnrutamientoReglas(EstrategiaEnrutamiento):
    """Heuristica simple de respaldo: puntaje fijo por tipo de persona.

    Sin aleatoriedad — util como fallback determinista cuando no se
    dispone (o no se confia) del motor genetico.
    """

    _PUNTAJE_POR_TIPO: dict[TipoPersona, float] = {
        TipoPersona.NATURAL: 50.0,
        TipoPersona.JURIDICA: 70.0,
    }

    def sugerir(
        self, tipo_persona: TipoPersona, detalle_solicitud: str
    ) -> SugerenciaDependencia:
        return SugerenciaDependencia(
            dependencia=_dependencia_por_tipo(tipo_persona),
            puntaje=self._PUNTAJE_POR_TIPO[tipo_persona],
        )


class EnrutamientoGenetico(EstrategiaEnrutamiento):
    """Usa ``AlgoritmoGenetico`` para variar el puntaje de prioridad.

    Genera una llave evolutiva (``generar_llave``) y normaliza su
    "fitness" (suma de valores de letra A-Z) a una escala 0-100. La
    dependencia sugerida sigue la misma regla de negocio que
    ``EnrutamientoReglas``: el motor genetico aporta la variabilidad del
    puntaje, no la decision de a que area va la solicitud.
    """

    def __init__(self, motor: AlgoritmoGenetico | None = None) -> None:
        self._motor: AlgoritmoGenetico = motor or AlgoritmoGenetico(
            tamano_poblacion=8,
            longitud_llave=10,
            mutacion=Mutacion(tasa=0.1),
        )

    def sugerir(
        self, tipo_persona: TipoPersona, detalle_solicitud: str
    ) -> SugerenciaDependencia:
        llave: str = self._motor.generar_llave()
        return SugerenciaDependencia(
            dependencia=_dependencia_por_tipo(tipo_persona),
            puntaje=self._puntaje_desde_llave(llave),
        )

    @staticmethod
    def _puntaje_desde_llave(llave: str) -> float:
        """Normaliza una llave evolutiva (A-Z) a un puntaje en [0, 100]."""
        if not llave:
            return PUNTAJE_MIN
        maximo_por_letra = ord("Z") - ord("A")
        suma = sum(ord(letra) - ord("A") for letra in llave)
        puntaje = (suma / (maximo_por_letra * len(llave))) * PUNTAJE_MAX
        return round(puntaje, 2)


class SugerenciaDependenciaService:
    """Orquesta la estrategia de enrutamiento configurada (MDP-10)."""

    def __init__(self, estrategia: EstrategiaEnrutamiento | None = None) -> None:
        self._estrategia: EstrategiaEnrutamiento = estrategia or EnrutamientoGenetico()

    def sugerir(
        self, tipo_persona: TipoPersona, detalle_solicitud: str
    ) -> SugerenciaDependencia:
        """Sugiere dependencia y puntaje para una solicitud aun no derivada."""
        return self._estrategia.sugerir(tipo_persona, detalle_solicitud)


@lru_cache(maxsize=1)
def get_sugerencia_dependencia_service() -> SugerenciaDependenciaService:
    """Provee la instancia singleton del servicio (estrategia genetica)."""
    return SugerenciaDependenciaService()


__all__ = [
    "PUNTAJE_MIN",
    "PUNTAJE_MAX",
    "SugerenciaDependencia",
    "EstrategiaEnrutamiento",
    "EnrutamientoReglas",
    "EnrutamientoGenetico",
    "SugerenciaDependenciaService",
    "get_sugerencia_dependencia_service",
]
