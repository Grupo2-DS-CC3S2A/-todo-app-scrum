"""Tests unitarios para DocumentoFactory (Factory Method, MDP-15)."""

from __future__ import annotations

import pytest

from src.excepciones.errors import DocumentoInvalidoError
from src.modelos.documento_solicitante import (
    DocumentoFactory,
    SolicitudPersonaJuridica,
    SolicitudPersonaNatural,
)
from src.modelos.tipo_persona import TipoPersona


class TestDocumentoFactoryPersonaNatural:
    def test_crea_solicitud_persona_natural_con_dni_valido(self):
        documento = DocumentoFactory.crear(TipoPersona.NATURAL, "40392536")
        assert isinstance(documento, SolicitudPersonaNatural)
        assert documento.dni == "40392536"
        assert documento.tipo_persona == TipoPersona.NATURAL

    @pytest.mark.parametrize("dni_invalido", ["1234567", "123456789", "abcdefgh", ""])
    def test_dni_invalido_lanza_documento_invalido_error(self, dni_invalido: str):
        with pytest.raises(DocumentoInvalidoError):
            DocumentoFactory.crear(TipoPersona.NATURAL, dni_invalido)


class TestDocumentoFactoryPersonaJuridica:
    def test_crea_solicitud_persona_juridica_con_ruc_valido(self):
        documento = DocumentoFactory.crear(TipoPersona.JURIDICA, "20123456789")
        assert isinstance(documento, SolicitudPersonaJuridica)
        assert documento.ruc == "20123456789"
        assert documento.tipo_persona == TipoPersona.JURIDICA

    @pytest.mark.parametrize(
        "ruc_invalido", ["2012345678", "201234567891", "abcdefghijk", ""]
    )
    def test_ruc_invalido_lanza_documento_invalido_error(self, ruc_invalido: str):
        with pytest.raises(DocumentoInvalidoError):
            DocumentoFactory.crear(TipoPersona.JURIDICA, ruc_invalido)


class TestDocumentoFactoryAmbasRamas:
    """CA-03 (MDP-15): un solo test parametrizado cubre ambas ramas de la factory."""

    @pytest.mark.parametrize(
        ("tipo", "numero_documento", "clase_esperada"),
        [
            (TipoPersona.NATURAL, "40392536", SolicitudPersonaNatural),
            (TipoPersona.JURIDICA, "20123456789", SolicitudPersonaJuridica),
        ],
    )
    def test_factory_retorna_la_subclase_correcta(
        self, tipo: TipoPersona, numero_documento: str, clase_esperada: type
    ):
        documento = DocumentoFactory.crear(tipo, numero_documento)
        assert type(documento) is clase_esperada
