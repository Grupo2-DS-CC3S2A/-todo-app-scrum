"""Tests de integración para los endpoints HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestEndpointHealth:
    def test_health_retorna_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
