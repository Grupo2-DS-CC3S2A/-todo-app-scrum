"""Tests unitarios para el modelo TipoPersona."""

from __future__ import annotations

import pytest

from src.modelos.tipo_persona import TipoPersona


class TestTipoPersona:
    def test_tiene_exactamente_dos_valores(self):
        assert {m.name for m in TipoPersona} == {"NATURAL", "JURIDICA"}

    def test_valor_natural_coincide_con_esquema_supabase(self):
        assert TipoPersona.NATURAL.value == "NATURAL"

    def test_valor_juridica_coincide_con_esquema_supabase(self):
        assert TipoPersona.JURIDICA.value == "JURIDICA"

    def test_es_subclase_de_str_para_serializar_directo(self):
        assert isinstance(TipoPersona.NATURAL, str)

    @pytest.mark.parametrize("valor", ["NATURAL", "JURIDICA"])
    def test_se_construye_desde_el_valor_string(self, valor: str):
        assert TipoPersona(valor).value == valor

    def test_valor_invalido_lanza_value_error(self):
        with pytest.raises(ValueError):
            TipoPersona("EXTRANJERA")
