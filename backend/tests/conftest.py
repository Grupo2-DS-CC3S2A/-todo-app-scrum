"""Fixtures compartidos entre todos los módulos de tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Generator

import src.main as _main_module
import src.servicios.auth_service as _auth_svc_module
from src.main import app
from src.repositorios.solicitud_repo import RepositorioSolicitudEnMemoria
from src.repositorios.usuario_repo import RepositorioUsuarioEnMemoria
from src.servicios.auth_service import get_auth_service
from src.servicios.solicitud_service import SolicitudService, get_solicitud_service
from src.utilidades.algoritmo_genetico import AlgoritmoGenetico, Mutacion


@pytest.fixture(autouse=True, scope="session")
def usar_repo_en_memoria_para_tests():
    """Sustituye repositorios Supabase por adaptadores in-memory durante
    la sesion de tests, no requiere credenciales de Supabase en CI/CD.

    - usuario: parcha el nombre importado en auth_service (namespace del importador).
    - solicitud: registrado en app.dependency_overrides para que todo
      TestClient(app) (e.g. test_auth.py y test_scrum25.py) use el
      adaptador in-memory, prescindiendo de supabase_key.
    - solicitud (repositorio crudo): parcha el nombre importado en main
      (GET /health lo invoca directo, sin Depends) para que no intente
      conectarse a Supabase durante los tests.
    """
    # Limpia get_auth_service sin borrar usuario_repositorio
    _original_usuario = _auth_svc_module.get_usuario_repository
    _auth_svc_module.get_usuario_repository = RepositorioUsuarioEnMemoria
    get_auth_service.cache_clear()

    # Limpia get_solicitud_service del servicio solicitud para todo TestClient
    _mem_solicitud_service = SolicitudService()
    app.dependency_overrides[get_solicitud_service] = lambda: _mem_solicitud_service
    get_solicitud_service.cache_clear()

    # Limpia get_solicitud_repository (usado directamente por GET /health)
    _original_solicitud_repo = _main_module.get_solicitud_repository
    _mem_solicitud_repo = RepositorioSolicitudEnMemoria()
    _main_module.get_solicitud_repository = lambda: _mem_solicitud_repo

    yield

    _auth_svc_module.get_usuario_repository = _original_usuario
    get_auth_service.cache_clear()
    app.dependency_overrides.pop(get_solicitud_service, None)
    get_solicitud_service.cache_clear()
    _main_module.get_solicitud_repository = _original_solicitud_repo


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
    _anterior = app.dependency_overrides.get(get_solicitud_service)
    app.dependency_overrides[get_solicitud_service] = lambda: solicitud_service
    with TestClient(app) as c:
        yield c
    # Restaura sólo la clave modificada
    if _anterior is not None:
        app.dependency_overrides[get_solicitud_service] = _anterior
    # No destruye otros overrides, sólo hace pop
    else:
        app.dependency_overrides.pop(get_solicitud_service, None)
