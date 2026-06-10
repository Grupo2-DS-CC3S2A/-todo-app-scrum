"""Fixtures compartidos entre todos los módulos de tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.servicios.solicitud_service import SolicitudService, get_solicitud_service
from src.servicios.voto_service import VotoService, get_voto_service
from src.utilidades.algoritmo_genetico import AlgoritmoGenetico, Mutacion


@pytest.fixture
def algoritmo() -> AlgoritmoGenetico:
    return AlgoritmoGenetico(
        tamano_poblacion=10,
        longitud_llave=8,
        mutacion=Mutacion(tasa=0.125),
    )


@pytest.fixture
def voto_service(algoritmo: AlgoritmoGenetico) -> VotoService:
    return VotoService(algoritmo=algoritmo)


@pytest.fixture
def solicitud_service() -> SolicitudService:
    return SolicitudService()


@pytest.fixture
def client(voto_service: VotoService, solicitud_service: SolicitudService) -> TestClient:
    app.dependency_overrides[get_voto_service] = lambda: voto_service
    app.dependency_overrides[get_solicitud_service] = lambda: solicitud_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
