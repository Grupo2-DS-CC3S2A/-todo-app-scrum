"""Tests de integración para los endpoints de administración."""

from __future__ import annotations

from fastapi.testclient import TestClient

_PAYLOAD_VALIDO = {
    "usuario_id": "usr-001",
    "detalle_solicitud": "Solicitud de derivación de prueba con suficiente detalle",
    "dependencia_asignada": "MesaDePartes",
    "tipo_persona": "NATURAL",
    "numero_documento": "40392536",
}
_TOKEN = "token-de-prueba"


class TestEndpointDerivar:
    def test_sin_token_retorna_403(self, client: TestClient):
        resp = client.post("/api/admin/solicitudes/derivar", json=_PAYLOAD_VALIDO)
        assert resp.status_code == 403

    def test_token_incorrecto_retorna_403(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=_PAYLOAD_VALIDO,
            headers={"X-Admin-Token": "token-incorrecto"},
        )
        assert resp.status_code == 403

    def test_derivacion_exitosa_retorna_201(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=_PAYLOAD_VALIDO,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 201

    def test_respuesta_contiene_campos_solicitud(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        datos = client.post(
            "/api/admin/solicitudes/derivar",
            json=_PAYLOAD_VALIDO,
            headers={"X-Admin-Token": _TOKEN},
        ).json()
        assert "id" in datos
        assert datos["estado"] == "Pendiente"
        assert datos["dependencia_asignada"] == "MesaDePartes"
        assert datos["tipo_persona"] == "NATURAL"

    def test_derivacion_persona_juridica_retorna_tipo_persona(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {
            **_PAYLOAD_VALIDO,
            "tipo_persona": "JURIDICA",
            "numero_documento": "20123456789",
        }
        datos = client.post(
            "/api/admin/solicitudes/derivar",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        ).json()
        assert datos["tipo_persona"] == "JURIDICA"

    def test_payload_invalido_retorna_422(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json={"usuario_id": "x"},
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422

    def test_payload_sin_tipo_persona_retorna_422(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {k: v for k, v in _PAYLOAD_VALIDO.items() if k != "tipo_persona"}
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422

    def test_payload_sin_numero_documento_retorna_422(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {k: v for k, v in _PAYLOAD_VALIDO.items() if k != "numero_documento"}
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422

    def test_dni_invalido_para_persona_natural_retorna_422(
        self, client: TestClient, monkeypatch
    ):
        """MDP-15 CA: numero_documento que no cumple el patron DNI se rechaza."""
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {**_PAYLOAD_VALIDO, "numero_documento": "123"}
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422

    def test_ruc_invalido_para_persona_juridica_retorna_422(
        self, client: TestClient, monkeypatch
    ):
        """MDP-15 CA: un DNI de 8 digitos no es un RUC valido para Juridica."""
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {
            **_PAYLOAD_VALIDO,
            "tipo_persona": "JURIDICA",
            "numero_documento": "40392536",
        }
        resp = client.post(
            "/api/admin/solicitudes/derivar",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422


class TestEndpointSugerirDependencia:
    """MDP-10: endpoint que expone la sugerencia antes de derivar."""

    _PAYLOAD_SUGERENCIA = {
        "tipo_persona": "NATURAL",
        "detalle_solicitud": "Solicitud de prueba con suficiente detalle",
    }

    def test_sin_token_retorna_403(self, client: TestClient):
        resp = client.post(
            "/api/admin/solicitudes/sugerir-dependencia",
            json=self._PAYLOAD_SUGERENCIA,
        )
        assert resp.status_code == 403

    def test_sugerencia_natural_retorna_mesa_de_partes(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.post(
            "/api/admin/solicitudes/sugerir-dependencia",
            json=self._PAYLOAD_SUGERENCIA,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 200
        datos = resp.json()
        assert datos["dependencia"] == "MesaDePartes"
        assert 0.0 <= datos["puntaje"] <= 100.0

    def test_sugerencia_juridica_retorna_asesoria_legal(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        payload = {**self._PAYLOAD_SUGERENCIA, "tipo_persona": "JURIDICA"}
        resp = client.post(
            "/api/admin/solicitudes/sugerir-dependencia",
            json=payload,
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 200
        assert resp.json()["dependencia"] == "AsesoriaLegal"

    def test_payload_invalido_retorna_422(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.post(
            "/api/admin/solicitudes/sugerir-dependencia",
            json={"tipo_persona": "NATURAL"},
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 422

    def test_no_persiste_ninguna_solicitud(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        headers = {"X-Admin-Token": _TOKEN}
        antes = client.get("/api/admin/solicitudes/", headers=headers).json()
        client.post(
            "/api/admin/solicitudes/sugerir-dependencia",
            json=self._PAYLOAD_SUGERENCIA,
            headers=headers,
        )
        despues = client.get("/api/admin/solicitudes/", headers=headers).json()
        assert len(despues) == len(antes)


class TestEndpointObtenerSolicitud:
    def test_obtener_solicitud_existente(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        headers = {"X-Admin-Token": _TOKEN}
        creada = client.post(
            "/api/admin/solicitudes/derivar",
            json=_PAYLOAD_VALIDO,
            headers=headers,
        ).json()
        resp = client.get(f"/api/admin/solicitudes/{creada['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == creada["id"]

    def test_obtener_solicitud_inexistente_retorna_404(
        self, client: TestClient, monkeypatch
    ):
        monkeypatch.setenv("ADMIN_TOKEN", _TOKEN)
        resp = client.get(
            "/api/admin/solicitudes/id-no-existe",
            headers={"X-Admin-Token": _TOKEN},
        )
        assert resp.status_code == 404
