"""Fixtures compartidos entre todos los módulos de tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Generator

import src.servicios.auth_service as _auth_svc_module
from src.main import app
from src.repositorios.usuario_repo import RepositorioUsuarioEnMemoria
from src.servicios.auth_service import get_auth_service
from src.servicios.solicitud_service import SolicitudService, get_solicitud_service
from src.utilidades.algoritmo_genetico import AlgoritmoGenetico, Mutacion


@pytest.fixture(autouse=True, scope="session")
def usar_repo_en_memoria_para_tests():
    """Sustituye RepositorioUsuarioSupabase por RepositorioUsuarioEnMemoria en
    la sesion de tests, sin tocar los archivos individuales test.

    Se parchea el nombre importado en auth_service, no el módulo origen, ya que
    Python resuelve el nombre en el namespace del importador.
    """
    _original = _auth_svc_module.get_usuario_repository
    _auth_svc_module.get_usuario_repository = RepositorioUsuarioEnMemoria
    get_auth_service.cache_clear()
    yield
    _auth_svc_module.get_usuario_repository = _original
    get_auth_service.cache_clear()


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
