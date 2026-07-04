"""Tests para el Strategy de enrutamiento y SugerenciaDependenciaService (MDP-10)."""

from __future__ import annotations

from src.modelos.solicitud import Dependencia
from src.modelos.tipo_persona import TipoPersona
from src.servicios.enrutamiento_service import (
    PUNTAJE_MAX,
    PUNTAJE_MIN,
    EnrutamientoGenetico,
    EnrutamientoReglas,
    SugerenciaDependencia,
    SugerenciaDependenciaService,
)

_DETALLE = "Solicitud de prueba con suficiente detalle para el enrutamiento"


class TestEnrutamientoReglas:
    """TASK-006: la estrategia de reglas se prueba de forma aislada."""

    def test_persona_natural_sugiere_mesa_de_partes(self):
        estrategia = EnrutamientoReglas()
        sugerencia = estrategia.sugerir(TipoPersona.NATURAL, _DETALLE)
        assert sugerencia.dependencia == Dependencia.MESA_DE_PARTES

    def test_persona_juridica_sugiere_asesoria_legal(self):
        estrategia = EnrutamientoReglas()
        sugerencia = estrategia.sugerir(TipoPersona.JURIDICA, _DETALLE)
        assert sugerencia.dependencia == Dependencia.ASESORIA_LEGAL

    def test_puntaje_es_determinista_para_el_mismo_tipo(self):
        estrategia = EnrutamientoReglas()
        s1 = estrategia.sugerir(TipoPersona.NATURAL, _DETALLE)
        s2 = estrategia.sugerir(TipoPersona.NATURAL, "otro detalle distinto aqui")
        assert s1.puntaje == s2.puntaje

    def test_puntaje_dentro_del_rango_valido(self):
        estrategia = EnrutamientoReglas()
        for tipo in TipoPersona:
            sugerencia = estrategia.sugerir(tipo, _DETALLE)
            assert PUNTAJE_MIN <= sugerencia.puntaje <= PUNTAJE_MAX


class TestEnrutamientoGenetico:
    """TASK-006: la estrategia genetica se prueba de forma aislada."""

    def test_persona_natural_sugiere_mesa_de_partes(self):
        estrategia = EnrutamientoGenetico()
        sugerencia = estrategia.sugerir(TipoPersona.NATURAL, _DETALLE)
        assert sugerencia.dependencia == Dependencia.MESA_DE_PARTES

    def test_persona_juridica_sugiere_asesoria_legal(self):
        estrategia = EnrutamientoGenetico()
        sugerencia = estrategia.sugerir(TipoPersona.JURIDICA, _DETALLE)
        assert sugerencia.dependencia == Dependencia.ASESORIA_LEGAL

    def test_puntaje_dentro_del_rango_valido(self):
        estrategia = EnrutamientoGenetico()
        for _ in range(20):
            sugerencia = estrategia.sugerir(TipoPersona.NATURAL, _DETALLE)
            assert PUNTAJE_MIN <= sugerencia.puntaje <= PUNTAJE_MAX

    def test_usa_el_motor_genetico_inyectado(self):
        """Verifica que la estrategia invoca AlgoritmoGenetico.generar_llave."""

        class _MotorFalso:
            def generar_llave(self) -> str:
                return "A" * 10  # letra minima -> puntaje minimo

        estrategia = EnrutamientoGenetico(motor=_MotorFalso())  # type: ignore[arg-type]
        sugerencia = estrategia.sugerir(TipoPersona.NATURAL, _DETALLE)
        assert sugerencia.puntaje == PUNTAJE_MIN

    def test_llave_de_letras_maximas_da_puntaje_maximo(self):
        class _MotorFalso:
            def generar_llave(self) -> str:
                return "Z" * 10

        estrategia = EnrutamientoGenetico(motor=_MotorFalso())  # type: ignore[arg-type]
        sugerencia = estrategia.sugerir(TipoPersona.JURIDICA, _DETALLE)
        assert sugerencia.puntaje == PUNTAJE_MAX


class TestSugerenciaDependenciaService:
    """TASK-007: el servicio usa la estrategia configurada (default: genetica)."""

    def test_dos_tipos_distintos_producen_sugerencias_distintas(self):
        servicio = SugerenciaDependenciaService()
        sugerencia_natural = servicio.sugerir(TipoPersona.NATURAL, _DETALLE)
        sugerencia_juridica = servicio.sugerir(TipoPersona.JURIDICA, _DETALLE)
        assert sugerencia_natural.dependencia != sugerencia_juridica.dependencia

    def test_usa_estrategia_de_reglas_si_se_inyecta(self):
        servicio = SugerenciaDependenciaService(estrategia=EnrutamientoReglas())
        sugerencia = servicio.sugerir(TipoPersona.NATURAL, _DETALLE)
        assert sugerencia == SugerenciaDependencia(
            dependencia=Dependencia.MESA_DE_PARTES, puntaje=50.0
        )

    def test_default_usa_estrategia_genetica(self):
        servicio = SugerenciaDependenciaService()
        sugerencia = servicio.sugerir(TipoPersona.NATURAL, _DETALLE)
        assert PUNTAJE_MIN <= sugerencia.puntaje <= PUNTAJE_MAX
