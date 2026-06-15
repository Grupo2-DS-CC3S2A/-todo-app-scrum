"""Fixtures compartidos entre todos los módulos de tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Generator

from src.main import app
from src.servicios.solicitud_service import SolicitudService, get_solicitud_service
from src.utilidades.algoritmo_genetico import AlgoritmoGenetico, Mutacion


@pytest.fixture
def algoritmo() -> AlgoritmoGenetico:
    return AlgoritmoGenetico(
        tamano_poblacion=10,
        longitud_llave=8,
        mutacion=Mutacion(tasa=0.125),
    )


@pytest.fixture
def solicitud_service() -> SolicitudService:
    return SolicitudService()


@pytest.fixture
def client(solicitud_service: SolicitudService) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_solicitud_service] = lambda: solicitud_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
