"""Tests unitarios para VotoService y el modelo VotoInput."""

from __future__ import annotations

import concurrent.futures

import pytest

from src.excepciones.errors import VotoDuplicadoError
from src.modelos.voto import VotoInput
from src.servicios.voto_service import VotoService


def _voto(dni: str = "12345678", candidato: int = 1) -> VotoInput:
    return VotoInput(dni_votante=dni, id_candidato=candidato)


class TestVotoInput:
    def test_dni_valido_acepta(self):
        v = VotoInput(dni_votante="12345678", id_candidato=1)
        assert v.dni_votante == "12345678"

    def test_dni_menos_de_8_digitos_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="1234567", id_candidato=1)

    def test_dni_mas_de_8_digitos_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="123456789", id_candidato=1)

    def test_dni_con_letras_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="1234567A", id_candidato=1)

    def test_dni_todo_igual_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="11111111", id_candidato=1)

    def test_dni_todo_ceros_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="00000000", id_candidato=1)

    def test_candidato_cero_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="12345678", id_candidato=0)

    def test_candidato_negativo_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="12345678", id_candidato=-1)

    def test_candidato_mayor_a_9999_rechaza(self):
        with pytest.raises(Exception):
            VotoInput(dni_votante="12345678", id_candidato=10000)

    def test_espacios_en_dni_se_eliminan(self):
        v = VotoInput(dni_votante=" 12345678 ", id_candidato=1)
        assert v.dni_votante == "12345678"


class TestVotoService:
    def test_registro_exitoso_devuelve_comprobante(self, voto_service: VotoService):
        comprobante = voto_service.registrar_voto(_voto())
        assert len(comprobante.hash_voto) == 64
        assert comprobante.clave_genetica
        assert comprobante.timestamp > 0

    def test_registro_incrementa_lista(self, voto_service: VotoService):
        voto_service.registrar_voto(_voto("12345678", 1))
        voto_service.registrar_voto(_voto("87654321", 2))
        assert len(voto_service.listar_votos()) == 2

    def test_voto_duplicado_lanza_excepcion(self):
        class _AlgoritmoFijo:
            def generar_llave(self) -> str:
                return "AAAAAAAA"

        servicio = VotoService(algoritmo=_AlgoritmoFijo())
        voto = _voto()
        servicio.registrar_voto(voto)
        with pytest.raises(VotoDuplicadoError):
            servicio.registrar_voto(voto)

    def test_listar_votos_devuelve_copia(self, voto_service: VotoService):
        voto_service.registrar_voto(_voto())
        lista1 = voto_service.listar_votos()
        lista2 = voto_service.listar_votos()
        assert lista1 == lista2
        assert lista1 is not lista2

    def test_thread_safety(self, voto_service: VotoService):
        dnis = [f"{10000000 + i}" for i in range(20)]
        votos = [_voto(dni=d, candidato=i + 1) for i, d in enumerate(dnis)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            resultados = list(executor.map(voto_service.registrar_voto, votos))

        assert len(resultados) == 20
        assert len(voto_service.listar_votos()) == 20
