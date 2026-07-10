"""Tests del modulo de tramites (consulta ciudadana y reemplazo).

Cubre que ``motivo_rechazo`` y ``fecha_resolucion`` viajen correctamente en
``GET /api/tramites/{dni}`` y ``GET /api/tramites/{dni}/buscar`` segun el
estado del tramite, y el reemplazo de un documento rechazado dentro del
plazo (``PATCH /api/tramites/{tramite_id}/reemplazo``). Usa un cliente
Supabase falso (duck-typed), siguiendo el mismo enfoque de fakes ya usado
en ``test_entidad_simulada.py``, ya que este router llama a
``get_client()`` directamente sin una capa de repositorio inyectable para
sus rutas de lectura.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

import src.rutas.tramites as tramites_module
from src.main import app

URL_TRAMITES = "/api/tramites"


class _FakeResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    """Duck-typed query builder: soporta tanto el encadenado de lectura
    (``select().eq()...``) como el de escritura (``update().eq()...``),
    mutando in-place las mismas filas que sostiene ``_FakeTable`` para que
    un ``obtener_por_id`` posterior en el mismo test vea el cambio."""

    def __init__(
        self, rows: list[dict[str, Any]], patch: dict[str, Any] | None = None
    ) -> None:
        self._rows = rows
        self._patch = patch

    def select(self, *_args: Any, **_kwargs: Any) -> "_FakeQuery":
        return self

    def eq(self, campo: str, valor: Any) -> "_FakeQuery":
        self._rows = [r for r in self._rows if r.get(campo) == valor]
        return self

    def gte(self, campo: str, valor: Any) -> "_FakeQuery":
        self._rows = [r for r in self._rows if r.get(campo) >= valor]
        return self

    def lte(self, campo: str, valor: Any) -> "_FakeQuery":
        self._rows = [r for r in self._rows if r.get(campo) <= valor]
        return self

    def limit(self, n: int) -> "_FakeQuery":
        self._rows = self._rows[:n]
        return self

    def order(self, *_args: Any, **_kwargs: Any) -> "_FakeQuery":
        return self

    def execute(self) -> _FakeResult:
        if self._patch is not None:
            for row in self._rows:
                row.update(self._patch)
        return _FakeResult([dict(r) for r in self._rows])


class _FakeTable:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def select(self, *_args: Any, **_kwargs: Any) -> _FakeQuery:
        return _FakeQuery(list(self._rows))

    def update(self, patch: dict[str, Any]) -> _FakeQuery:
        return _FakeQuery(list(self._rows), patch=patch)


class _FakeClient:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def schema(self, _nombre: str) -> "_FakeClient":
        return self

    def table(self, _nombre: str) -> _FakeTable:
        return _FakeTable(self._rows)


_TRAMITES: list[dict[str, Any]] = [
    {
        "id": 1,
        "dni": "40392536",
        "nro_documento": "10001",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Tesoreria",
        "estado_documento": "EN TRAMITE",
        "fecha_tramite": "2026-07-01",
        "fecha_respuesta": "2026-07-31",
        "contenedor": "http://signature/api/documentos/1/download-signed",
        "motivo_rechazo": None,
        "fecha_resolucion": None,
    },
    {
        "id": 2,
        "dni": "40392536",
        "nro_documento": "10002",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Tesoreria",
        "estado_documento": "ACEPTADO",
        "fecha_tramite": "2026-06-01",
        "fecha_respuesta": "2026-07-01",
        "contenedor": "http://signature/api/documentos/2/download-signed",
        "motivo_rechazo": None,
        "fecha_resolucion": "2026-06-15",
    },
    {
        "id": 3,
        "dni": "40392536",
        "nro_documento": "10003",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Logistica",
        "estado_documento": "RECHAZADO",
        "fecha_tramite": "2026-05-01",
        "fecha_respuesta": "2026-05-31",
        "contenedor": "http://signature/api/documentos/3/download-signed",
        "motivo_rechazo": "El documento no incluye la firma del representante legal.",
        "fecha_resolucion": "2026-05-20",
    },
    {
        "id": 4,
        "dni": "40392536",
        "nro_documento": "10004",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Tesoreria",
        "estado_documento": "RECHAZADO",
        "fecha_tramite": "2026-06-01",
        "fecha_respuesta": (date.today() + timedelta(days=5)).isoformat(),
        "contenedor": "http://signature/api/documentos/4/download-signed",
        "motivo_rechazo": "Falta firma legal",
        "fecha_resolucion": "2026-06-05",
    },
    {
        "id": 5,
        "dni": "40392536",
        "nro_documento": "10005",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Tesoreria",
        "estado_documento": "RECHAZADO",
        "fecha_tramite": "2026-06-01",
        "fecha_respuesta": (date.today() - timedelta(days=1)).isoformat(),
        "contenedor": "http://signature/api/documentos/5/download-signed",
        "motivo_rechazo": "Falta firma legal",
        "fecha_resolucion": "2026-06-05",
    },
    {
        "id": 6,
        "dni": "40392536",
        "nro_documento": "10006",
        "tipo_documento": "SOLICITUD",
        "dependencia": "Tesoreria",
        "estado_documento": "RECHAZADO",
        "fecha_tramite": "2026-06-01",
        "fecha_respuesta": date.today().isoformat(),
        "contenedor": "http://signature/api/documentos/6/download-signed",
        "motivo_rechazo": "Falta firma legal",
        "fecha_resolucion": "2026-06-05",
    },
]


@pytest.fixture(autouse=True)
def _fake_supabase_client(monkeypatch: pytest.MonkeyPatch) -> None:
    # Copia profunda: el reemplazo muta filas in-place, y las filas de
    # ``_TRAMITES`` son compartidas a nivel de modulo entre tests.
    filas_frescas = [dict(t) for t in _TRAMITES]
    monkeypatch.setattr(
        tramites_module, "get_client", lambda: _FakeClient(filas_frescas)
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _por_id(tramite_id: int, tramites: list[dict[str, Any]]) -> dict[str, Any]:
    return next(t for t in tramites if t["id"] == tramite_id)


class TestConsultaPorDni:
    """GET /api/tramites/{dni}"""

    def test_en_tramite_no_muestra_motivo_ni_fecha_resolucion(
        self, client: TestClient
    ) -> None:
        resp = client.get(f"{URL_TRAMITES}/40392536")
        assert resp.status_code == 200
        tramite = _por_id(1, resp.json())
        assert tramite["motivo_rechazo"] is None
        assert tramite["fecha_resolucion"] is None

    def test_aceptado_no_muestra_motivo_pero_si_fecha_resolucion(
        self, client: TestClient
    ) -> None:
        resp = client.get(f"{URL_TRAMITES}/40392536")
        assert resp.status_code == 200
        tramite = _por_id(2, resp.json())
        assert tramite["motivo_rechazo"] is None
        assert tramite["fecha_resolucion"] == "2026-06-15"

    def test_rechazado_muestra_motivo_y_fecha_resolucion(
        self, client: TestClient
    ) -> None:
        resp = client.get(f"{URL_TRAMITES}/40392536")
        assert resp.status_code == 200
        tramite = _por_id(3, resp.json())
        assert tramite["motivo_rechazo"] == (
            "El documento no incluye la firma del representante legal."
        )
        assert tramite["fecha_resolucion"] == "2026-05-20"


class TestBusquedaConFiltros:
    """GET /api/tramites/{dni}/buscar"""

    def test_en_tramite_no_muestra_motivo_ni_fecha_resolucion(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            f"{URL_TRAMITES}/40392536/buscar",
            params={
                "tipo_documento": "SOLICITUD",
                "fecha_desde": "2026-07-01",
                "fecha_hasta": "2026-07-31",
            },
        )
        assert resp.status_code == 200
        tramites = resp.json()
        assert len(tramites) == 1
        assert tramites[0]["id"] == 1
        assert tramites[0]["motivo_rechazo"] is None
        assert tramites[0]["fecha_resolucion"] is None

    def test_rechazado_muestra_motivo_y_fecha_resolucion(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            f"{URL_TRAMITES}/40392536/buscar",
            params={
                "tipo_documento": "SOLICITUD",
                "fecha_desde": "2026-05-01",
                "fecha_hasta": "2026-05-31",
            },
        )
        assert resp.status_code == 200
        tramites = resp.json()
        assert len(tramites) == 1
        assert tramites[0]["motivo_rechazo"] == (
            "El documento no incluye la firma del representante legal."
        )
        assert tramites[0]["fecha_resolucion"] == "2026-05-20"


class TestReemplazoTramite:
    """PATCH /api/tramites/{tramite_id}/reemplazo."""

    def test_reemplazo_dentro_del_plazo_reabre_a_en_tramite(
        self, client: TestClient
    ) -> None:
        resp = client.patch(
            f"{URL_TRAMITES}/4/reemplazo",
            json={
                "dni": "40392536",
                "contenedor": "http://signature/api/documentos/4/download-signed-v2",
            },
        )
        assert resp.status_code == 200
        tramite = resp.json()
        assert tramite["estado_documento"] == "EN TRAMITE"
        assert tramite["motivo_rechazo"] is None
        assert tramite["fecha_resolucion"] is None
        assert tramite["contenedor"] == (
            "http://signature/api/documentos/4/download-signed-v2"
        )
        # El plazo original no se reinicia ni se toca fecha_tramite.
        assert tramite["fecha_tramite"] == "2026-06-01"
        assert tramite["fecha_respuesta"] == _por_id(4, _TRAMITES)["fecha_respuesta"]

    def test_reemplazo_con_dni_que_no_coincide_devuelve_404(
        self, client: TestClient
    ) -> None:
        resp = client.patch(
            f"{URL_TRAMITES}/4/reemplazo",
            json={"dni": "99999999", "contenedor": "http://signature/x"},
        )
        assert resp.status_code == 404

    def test_reemplazo_sobre_tramite_no_rechazado_devuelve_409(
        self, client: TestClient
    ) -> None:
        # id=1 esta "EN TRAMITE", no "RECHAZADO".
        resp = client.patch(
            f"{URL_TRAMITES}/1/reemplazo",
            json={"dni": "40392536", "contenedor": "http://signature/x"},
        )
        assert resp.status_code == 409

    def test_reemplazo_con_plazo_vencido_devuelve_409(self, client: TestClient) -> None:
        # id=5 tiene fecha_respuesta = ayer.
        resp = client.patch(
            f"{URL_TRAMITES}/5/reemplazo",
            json={"dni": "40392536", "contenedor": "http://signature/x"},
        )
        assert resp.status_code == 409

    def test_reemplazo_el_mismo_dia_del_vencimiento_es_permitido(
        self, client: TestClient
    ) -> None:
        # id=6 tiene fecha_respuesta = hoy: el limite es inclusivo.
        resp = client.patch(
            f"{URL_TRAMITES}/6/reemplazo",
            json={"dni": "40392536", "contenedor": "http://signature/x"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado_documento"] == "EN TRAMITE"
