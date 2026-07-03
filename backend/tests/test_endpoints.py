"""Tests de integración para los endpoints HTTP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import src.main as main_module


class TestEndpointHealth:
    def test_health_retorna_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_retorna_503_si_supabase_no_responde(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        class _RepoCaido:
            def contar(self) -> int:
                raise ConnectionError("Supabase inalcanzable")

        monkeypatch.setattr(
            main_module, "get_solicitud_repository", lambda: _RepoCaido()
        )
        resp = client.get("/health")
        assert resp.status_code == 503
