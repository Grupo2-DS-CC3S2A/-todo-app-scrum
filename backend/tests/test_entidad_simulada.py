"""Tests del modulo de entidad revisora (entidad_simulada).

Cubre dos capas:

- Ruta HTTP: el gate de rol (``require_roles``) bloquea a ciudadanos y a
  quien no envia token, sin necesidad de Supabase real.
- Facade: el alcance por dependencia de un operador (solo su propia
  dependencia) y el bypass de administrador, usando un repositorio y un
  adaptador de firma falsos en memoria.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.excepciones.errors import PermisoDenegadoError
from src.main import app
from src.modelos.usuario import RolUsuario, Usuario
from src.repositorios.usuario_repo import RepositorioUsuarioEnMemoria
from src.rutas.entidad_simulada import EntidadSimuladaFacade
from src.servicios.auth_service import get_auth_service

from src.config import settings

URL_DOCUMENTOS = "/api/entidad-simulada/documentos"
URL_LOGIN = "/api/auth/login"
URL_REGISTER = "/api/auth/register"

ADMIN_USERNAME = settings.admin_seed_username
ADMIN_PASSWORD = settings.admin_seed_password


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_usuarios_y_reseedea():
    repo = RepositorioUsuarioEnMemoria()
    with repo._lock:
        repo._por_id.clear()
        repo._por_username.clear()
    auth = get_auth_service()
    auth._seed_admin_si_falta()
    yield


def _login(client: TestClient, username: str, password: str):
    return client.post(URL_LOGIN, json={"username": username, "password": password})


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _token_admin(client: TestClient) -> str:
    resp = _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _crear_ciudadano(client: TestClient, admin_token: str) -> str:
    resp = client.post(
        URL_REGISTER,
        json={
            "username": "ciudadano01",
            "password": "Ciudadano123!",
            "rol": "ciudadano",
        },
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    login = _login(client, "ciudadano01", "Ciudadano123!")
    assert login.status_code == 200
    return str(login.json()["access_token"])


class TestGateDeRolEnRuta:
    """El modulo no debe ser accesible salvo para admin/operador (HU: solo
    la entidad revisora entra a esta seccion)."""

    def test_sin_token_devuelve_401(self, client: TestClient) -> None:
        resp = client.get(URL_DOCUMENTOS, params={"dependencia": "Tesoreria"})
        assert resp.status_code == 401

    def test_ciudadano_devuelve_403(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        ciudadano_token = _crear_ciudadano(client, admin_token)
        resp = client.get(
            URL_DOCUMENTOS,
            params={"dependencia": "Tesoreria"},
            headers=_auth_header(ciudadano_token),
        )
        assert resp.status_code == 403


class _FakeRepo:
    """Repositorio en memoria: implementa la misma interfaz duck-typed que
    ``DocumentoTramitadoRepository`` sin tocar Supabase."""

    def __init__(self, documentos: list[dict]) -> None:
        self._documentos = documentos
        self.llamadas_por_dependencia: list[str] = []
        self.llamo_listar_todos = False

    def listar_por_dependencia(self, dependencia: str) -> list[dict]:
        self.llamadas_por_dependencia.append(dependencia)
        return [d for d in self._documentos if d["dependencia"] == dependencia]

    def listar_todos(self) -> list[dict]:
        self.llamo_listar_todos = True
        return list(self._documentos)

    def obtener_por_id(self, tramite_id: int) -> dict | None:
        return next((d for d in self._documentos if d["id"] == tramite_id), None)

    def borrar_por_id(self, tramite_id: int) -> None:
        self._documentos = [d for d in self._documentos if d["id"] != tramite_id]


class _FakeSignatureAdapter:
    def extraer_id_documento_firmado(self, contenedor_url: str) -> int:
        return 1

    def verificar_documento_guardado(self, signed_document_id: int) -> dict:
        return {"verified": True}

    def descargar_bytes(self, url: str) -> bytes:
        return b"contenido-de-prueba"

    def url_pdf_visible(self, signed_document_id: int) -> str:
        return "http://signature-service/pdf-visible"


_DOCUMENTOS = [
    {
        "id": 1,
        "dependencia": "Tesoreria",
        "nro_documento": "10001",
        "estado_documento": "EN TRAMITE",
        "fecha_tramite": "2026-07-01",
        "fecha_respuesta": "2026-07-31",
        "contenedor": "http://signature/api/documentos/1/download-signed",
    },
    {
        "id": 2,
        "dependencia": "Logistica",
        "nro_documento": "10002",
        "estado_documento": "EN TRAMITE",
        "fecha_tramite": "2026-07-02",
        "fecha_respuesta": "2026-08-01",
        "contenedor": "http://signature/api/documentos/2/download-signed",
    },
]


def _usuario(rol: RolUsuario, dependencia_asignada: str | None = None) -> Usuario:
    return Usuario(
        username=f"user-{rol.value}",
        password_hash="hash",
        rol=rol,
        dependencia_asignada=dependencia_asignada,
    )


@pytest.fixture
def facade() -> tuple[EntidadSimuladaFacade, _FakeRepo]:
    repo = _FakeRepo(list(_DOCUMENTOS))
    return EntidadSimuladaFacade(repo, _FakeSignatureAdapter()), repo


class TestAlcancePorDependenciaAlListar:
    def test_operador_ignora_parametro_y_usa_su_propia_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, repo = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        resultado = instancia.listar_documentos("Logistica", operador)

        assert repo.llamadas_por_dependencia == ["Tesoreria"]
        assert [d.id for d in resultado] == [1]

    def test_operador_sin_dependencia_asignada_lanza_permiso_denegado(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada=None)

        with pytest.raises(PermisoDenegadoError):
            instancia.listar_documentos("Tesoreria", operador)

    def test_admin_sin_filtro_lista_todas_las_dependencias(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, repo = facade
        admin = _usuario(RolUsuario.ADMIN)

        resultado = instancia.listar_documentos(None, admin)

        assert repo.llamo_listar_todos is True
        assert len(resultado) == 2

    def test_admin_puede_filtrar_por_dependencia_especifica(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, repo = facade
        admin = _usuario(RolUsuario.ADMIN)

        instancia.listar_documentos("Logistica", admin)

        assert repo.llamadas_por_dependencia == ["Logistica"]


class TestAccesoPorDocumentoIndividual:
    """Aplica a verificar_firma / generar_zip_documento / borrar_documento:
    un operador no puede operar sobre un documento de otra dependencia."""

    def test_operador_no_puede_verificar_documento_de_otra_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        with pytest.raises(PermisoDenegadoError):
            instancia.verificar_firma(2, operador)  # documento id=2 es Logistica

    def test_operador_puede_verificar_documento_de_su_propia_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        resultado = instancia.verificar_firma(1, operador)

        assert resultado.verificacion_correcta is True

    def test_admin_puede_verificar_documento_de_cualquier_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        admin = _usuario(RolUsuario.ADMIN)

        resultado = instancia.verificar_firma(2, admin)

        assert resultado.verificacion_correcta is True

    def test_operador_no_puede_borrar_documento_de_otra_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, repo = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        with pytest.raises(PermisoDenegadoError):
            instancia.borrar_documento(2, operador)
        assert repo.obtener_por_id(2) is not None

    def test_operador_puede_borrar_documento_de_su_propia_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, repo = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        instancia.borrar_documento(1, operador)

        assert repo.obtener_por_id(1) is None

    def test_operador_no_puede_generar_zip_de_otra_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        with pytest.raises(PermisoDenegadoError):
            instancia.generar_zip_documento(2, operador)

    def test_operador_puede_generar_zip_de_su_propia_dependencia(
        self, facade: tuple[EntidadSimuladaFacade, _FakeRepo]
    ) -> None:
        instancia, _ = facade
        operador = _usuario(RolUsuario.OPERADOR, dependencia_asignada="Tesoreria")

        filename, contenido = instancia.generar_zip_documento(1, operador)

        assert filename == "documento_10001.zip"
        assert len(contenido) > 0
