"""Tests de integración para los endpoints HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient


_VOTO_VALIDO = {"dni_votante": "12345678", "id_candidato": 1}


class TestEndpointHealth:
    def test_health_retorna_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestEndpointVotar:
    def test_voto_valido_retorna_201(self, client: TestClient):
        resp = client.post("/api/votar", json=_VOTO_VALIDO)
        assert resp.status_code == 201

    def test_respuesta_contiene_campos_comprobante(self, client: TestClient):
        resp = client.post("/api/votar", json=_VOTO_VALIDO)
        datos = resp.json()
        assert "hash_voto" in datos
        assert "clave_genetica" in datos
        assert "timestamp" in datos

    def test_hash_tiene_64_caracteres(self, client: TestClient):
        resp = client.post("/api/votar", json=_VOTO_VALIDO)
        assert len(resp.json()["hash_voto"]) == 64

    def test_dni_invalido_retorna_422(self, client: TestClient):
        resp = client.post("/api/votar", json={"dni_votante": "123", "id_candidato": 1})
        assert resp.status_code == 422

    def test_dni_con_letras_retorna_422(self, client: TestClient):
        resp = client.post("/api/votar", json={"dni_votante": "1234567A", "id_candidato": 1})
        assert resp.status_code == 422

    def test_candidato_cero_retorna_422(self, client: TestClient):
        resp = client.post("/api/votar", json={"dni_votante": "12345678", "id_candidato": 0})
        assert resp.status_code == 422

    def test_payload_vacio_retorna_422(self, client: TestClient):
        resp = client.post("/api/votar", json={})
        assert resp.status_code == 422

    def test_campo_extra_retorna_422(self, client: TestClient):
        resp = client.post("/api/votar", json={**_VOTO_VALIDO, "campo_extra": "x"})
        assert resp.status_code == 422


class TestEndpointAuditoria:
    def test_auditoria_retorna_200(self, client: TestClient):
        resp = client.get("/api/votos_audit")
        assert resp.status_code == 200

    def test_auditoria_sin_votos_retorna_total_cero(self, client: TestClient):
        datos = client.get("/api/votos_audit").json()
        assert datos["total"] == 0
        assert datos["votos_cifrados"] == []

    def test_auditoria_refleja_voto_registrado(self, client: TestClient):
        client.post("/api/votar", json=_VOTO_VALIDO)
        datos = client.get("/api/votos_audit").json()
        assert datos["total"] == 1
        assert len(datos["votos_cifrados"]) == 1

    def test_auditoria_acumula_multiples_votos(self, client: TestClient):
        client.post("/api/votar", json={"dni_votante": "12345678", "id_candidato": 1})
        client.post("/api/votar", json={"dni_votante": "87654321", "id_candidato": 2})
        datos = client.get("/api/votos_audit").json()
        assert datos["total"] == 2
