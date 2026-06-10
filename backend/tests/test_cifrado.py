"""Tests unitarios para el módulo de cifrado SHA-256."""

from __future__ import annotations

from src.utilidades.cifrado import aplicar_hash_sha256

_DNI = "12345678"
_CANDIDATO = 1
_LLAVE = "ABCDEFGH"


def test_digest_tiene_64_caracteres_hexadecimales():
    resultado = aplicar_hash_sha256(_DNI, _CANDIDATO, _LLAVE)
    assert len(resultado) == 64
    assert all(c in "0123456789abcdef" for c in resultado)


def test_mismo_input_produce_mismo_hash():
    h1 = aplicar_hash_sha256(_DNI, _CANDIDATO, _LLAVE)
    h2 = aplicar_hash_sha256(_DNI, _CANDIDATO, _LLAVE)
    assert h1 == h2


def test_llave_diferente_produce_hash_diferente():
    h1 = aplicar_hash_sha256(_DNI, _CANDIDATO, "AAAAAAAA")
    h2 = aplicar_hash_sha256(_DNI, _CANDIDATO, "BBBBBBBB")
    assert h1 != h2


def test_candidato_diferente_produce_hash_diferente():
    h1 = aplicar_hash_sha256(_DNI, 1, _LLAVE)
    h2 = aplicar_hash_sha256(_DNI, 2, _LLAVE)
    assert h1 != h2


def test_payload_con_caracteres_especiales():
    resultado = aplicar_hash_sha256("12345678", 99, "ABC!@#$%")
    assert len(resultado) == 64
