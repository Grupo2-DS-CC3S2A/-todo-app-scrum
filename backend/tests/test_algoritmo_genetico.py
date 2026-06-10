"""Tests unitarios para el módulo del algoritmo genético."""

from __future__ import annotations

import string

import pytest

from src.utilidades.algoritmo_genetico import (
    AlgoritmoGenetico,
    Cromosoma,
    Cruce,
    Mutacion,
    Poblacion,
)

_LONGITUD = 8
_ALFABETO = set(string.ascii_uppercase)


class TestCromosoma:
    def test_longitud_correcta(self):
        c = Cromosoma.aleatorio(_LONGITUD)
        assert len(c.genes) == _LONGITUD

    def test_genes_en_alfabeto_valido(self):
        c = Cromosoma.aleatorio(_LONGITUD)
        assert all(g in _ALFABETO for g in c.genes)

    def test_distintos_cromosomas_son_distintos_con_alta_probabilidad(self):
        muestras = {Cromosoma.aleatorio(_LONGITUD).genes for _ in range(50)}
        assert len(muestras) > 1


class TestPoblacion:
    def test_tamano_inicial_correcto(self):
        p = Poblacion.inicial(tamano=10, longitud_gen=_LONGITUD)
        assert len(p.individuos) == 10

    def test_poblacion_minima_dos_individuos(self):
        p = Poblacion.inicial(tamano=2, longitud_gen=_LONGITUD)
        assert len(p.individuos) == 2

    def test_tamano_menor_a_dos_lanza_excepcion(self):
        with pytest.raises(ValueError):
            Poblacion.inicial(tamano=1, longitud_gen=_LONGITUD)

    def test_seleccionar_padres_devuelve_dos_cromosomas_distintos(self):
        p = Poblacion.inicial(tamano=10, longitud_gen=_LONGITUD)
        padre1, padre2 = p.seleccionar_padres()
        assert isinstance(padre1, Cromosoma)
        assert isinstance(padre2, Cromosoma)
        assert padre1 is not padre2


class TestCruce:
    def test_hijo_tiene_longitud_correcta(self):
        p1 = Cromosoma(genes="AAAAAAAA")
        p2 = Cromosoma(genes="BBBBBBBB")
        hijo = Cruce.aplicar(p1, p2)
        assert len(hijo.genes) == _LONGITUD

    def test_single_point_crossover_en_mitad(self):
        p1 = Cromosoma(genes="AAAAAAAA")
        p2 = Cromosoma(genes="BBBBBBBB")
        hijo = Cruce.aplicar(p1, p2)
        assert hijo.genes == "AAAABBBB"

    def test_padres_de_distinta_longitud_lanza_excepcion(self):
        p1 = Cromosoma(genes="AAAA")
        p2 = Cromosoma(genes="BBBBBB")
        with pytest.raises(ValueError):
            Cruce.aplicar(p1, p2)


class TestMutacion:
    def test_tasa_cero_no_muta(self):
        mutacion = Mutacion(tasa=0.0)
        original = Cromosoma(genes="AAAAAAAA")
        resultado = mutacion.aplicar(original)
        assert resultado.genes == original.genes

    def test_tasa_uno_muta_todos_los_genes(self):
        mutacion = Mutacion(tasa=1.0)
        original = Cromosoma(genes="AAAAAAAA")
        resultado = mutacion.aplicar(original)
        assert len(resultado.genes) == _LONGITUD
        assert all(g in _ALFABETO for g in resultado.genes)

    def test_tasa_invalida_lanza_excepcion(self):
        mutacion = Mutacion(tasa=1.5)
        with pytest.raises(ValueError):
            mutacion.aplicar(Cromosoma(genes="AAAAAAAA"))

    def test_resultado_tiene_misma_longitud(self):
        mutacion = Mutacion(tasa=0.5)
        original = Cromosoma.aleatorio(_LONGITUD)
        resultado = mutacion.aplicar(original)
        assert len(resultado.genes) == _LONGITUD


class TestAlgoritmoGenetico:
    def test_generar_llave_tiene_longitud_correcta(self, algoritmo: AlgoritmoGenetico):
        llave = algoritmo.generar_llave()
        assert len(llave) == _LONGITUD

    def test_generar_llave_solo_mayusculas(self, algoritmo: AlgoritmoGenetico):
        llave = algoritmo.generar_llave()
        assert all(c in _ALFABETO for c in llave)

    def test_llaves_sucesivas_son_distintas_con_alta_probabilidad(
        self, algoritmo: AlgoritmoGenetico
    ):
        llaves = {algoritmo.generar_llave() for _ in range(30)}
        assert len(llaves) > 1
