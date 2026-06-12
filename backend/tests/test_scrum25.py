"""SCRUM-25 [QA] — Pruebas unitarias de login, tokens expirados y denegacion de accesos.

Mapeados directamente a los escenarios de PASOS.md:

  PASO 4  → credenciales invalidas devuelven error legible
  PASO 5  → login exitoso emite JWT con claims correctos
  PASO 8  → endpoints admin exigen JWT valido con rol admin
  PASO 10 → token expirado devuelve 401 / 403 segun el endpoint

Ademas cubre las ramas no ejercidas por test_auth.py para mantener
la cobertura de los modulos de autenticacion por encima del 85%:

  - Token sin claim ``sub``          → auth_deps.py:42
  - Token con usuario eliminado      → auth_deps.py:45-46
  - Token sin claim ``rol``          → auth_service.py:119
  - Hash malformado en verificacion  → auth_service.py:82-83
  - ``obtener_por_id`` inexistente   → usuario_repo.py:116
  - ``listar`` usuarios              → usuario_repo.py:124-125
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.config import settings
from src.excepciones.errors import TokenInvalidoError, UsuarioNoEncontradoError
from src.main import app
from src.modelos.usuario import RolUsuario
from src.repositorios.usuario_repo import RepositorioUsuarioEnMemoria
from src.servicios.auth_service import AuthService, get_auth_service

URL_LOGIN = "/api/auth/login"
URL_REGISTER = "/api/auth/register"
URL_ME = "/api/auth/me"
URL_ADMIN = "/api/admin/solicitudes"

ADMIN_USER = settings.admin_seed_username
ADMIN_PASS = settings.admin_seed_password


# ----------------------------------------------------------------- Fixtures


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_y_resembrar():
    """Resetea el repositorio singleton antes de cada test."""
    repo = RepositorioUsuarioEnMemoria()
    with repo._lock:
        repo._por_id.clear()
        repo._por_username.clear()
    get_auth_service()._seed_admin_si_falta()
    yield


def _token_admin(client: TestClient) -> str:
    resp = client.post(URL_LOGIN, json={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _jwt_personalizado(**claims) -> str:
    base = {
        "sub": "fake-id",
        "rol": RolUsuario.ADMIN.value,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    base.update(claims)
    return jwt.encode(base, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ============================================================= PASO 4 y 5
# Login correcto e incorrecto


class TestLogin:
    def test_login_exitoso_devuelve_bearer_jwt(self, client: TestClient) -> None:
        """PASO 5 — login exitoso emite JWT con tipo 'bearer'."""
        resp = client.post(URL_LOGIN, json={"username": ADMIN_USER, "password": ADMIN_PASS})
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["expires_in"] > 0

    def test_login_password_incorrecta_devuelve_401(self, client: TestClient) -> None:
        """PASO 4 — password incorrecta retorna 401 con mensaje de error."""
        resp = client.post(URL_LOGIN, json={"username": ADMIN_USER, "password": "mal"*5})
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "CredencialesInvalidasError"

    def test_login_usuario_inexistente_devuelve_401(self, client: TestClient) -> None:
        """PASO 4 — usuario inexistente no revela si existe o no."""
        resp = client.post(URL_LOGIN, json={"username": "fantasma", "password": "Password1!"})
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "CredencialesInvalidasError"

    def test_jwt_contiene_rol_y_sub(self, client: TestClient) -> None:
        """PASO 5 — el JWT emitido contiene los claims sub, rol y exp."""
        token = _token_admin(client)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["rol"] == RolUsuario.ADMIN.value
        assert "sub" in payload
        assert "exp" in payload


# ============================================================= PASO 10
# Tokens expirados


class TestTokensExpirados:
    def test_token_expirado_en_me_devuelve_401(self, client: TestClient) -> None:
        """PASO 10 — GET /api/auth/me con token expirado retorna 401."""
        ahora = datetime.now(tz=timezone.utc)
        expirado = jwt.encode(
            {
                "sub": "x",
                "rol": RolUsuario.ADMIN.value,
                "iat": int((ahora - timedelta(hours=25)).timestamp()),
                "exp": int((ahora - timedelta(hours=1)).timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        resp = client.get(URL_ME, headers=_bearer(expirado))
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "TokenInvalidoError"

    def test_token_expirado_en_admin_devuelve_403(self, client: TestClient) -> None:
        """PASO 10 — endpoints admin con token expirado retornan 403."""
        ahora = datetime.now(tz=timezone.utc)
        expirado = jwt.encode(
            {
                "sub": "x",
                "rol": RolUsuario.ADMIN.value,
                "iat": int((ahora - timedelta(hours=25)).timestamp()),
                "exp": int((ahora - timedelta(hours=1)).timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        resp = client.get(URL_ADMIN, headers=_bearer(expirado))
        assert resp.status_code == 403

    def test_token_sin_claim_sub_devuelve_401(self, client: TestClient) -> None:
        """Token valido pero sin claim 'sub' → 401 (auth_deps.py:42)."""
        sin_sub = _jwt_personalizado(sub="")
        resp = client.get(URL_ME, headers=_bearer(sin_sub))
        assert resp.status_code == 401

    def test_token_usuario_eliminado_devuelve_401(self, client: TestClient) -> None:
        """Token valido cuyo usuario ya no existe en el repo → 401 (auth_deps.py:45-46)."""
        token_huerfano = _jwt_personalizado(sub="id-que-no-existe-en-repo")
        resp = client.get(URL_ME, headers=_bearer(token_huerfano))
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "TokenInvalidoError"


# ============================================================= PASO 8 y 9
# Denegacion de accesos 401 / 403


class TestDenegacionAccesos:
    def test_me_sin_token_devuelve_401(self, client: TestClient) -> None:
        """PASO 8 — sin token el endpoint retorna 401."""
        resp = client.get(URL_ME)
        assert resp.status_code == 401

    def test_admin_sin_token_devuelve_403(self, client: TestClient) -> None:
        """PASO 8 — endpoint admin sin ninguna credencial retorna 403."""
        resp = client.get(URL_ADMIN)
        assert resp.status_code == 403

    def test_admin_con_rol_insuficiente_devuelve_403(self, client: TestClient) -> None:
        """PASO 8 — operador autenticado no puede acceder a rutas de admin."""
        admin_token = _token_admin(client)
        client.post(
            URL_REGISTER,
            json={"username": "op01", "password": "Operador123!", "rol": "operador"},
            headers=_bearer(admin_token),
        ).raise_for_status()
        op_token = client.post(
            URL_LOGIN, json={"username": "op01", "password": "Operador123!"}
        ).json()["access_token"]
        resp = client.get(URL_ADMIN, headers=_bearer(op_token))
        assert resp.status_code == 403
        assert resp.json()["tipo"] == "NoAutorizadoError"

    def test_register_sin_token_devuelve_401(self, client: TestClient) -> None:
        """Registrar usuario sin token de admin retorna 401."""
        resp = client.post(
            URL_REGISTER,
            json={"username": "nuevo", "password": "Password1!", "rol": "operador"},
        )
        assert resp.status_code == 401


# ============================================================= Servicio y repo
# Cobertura de ramas internas no alcanzadas via HTTP


class TestAuthServiceInterno:
    def test_verificar_password_con_hash_malformado_retorna_falso(self) -> None:
        """Hash corrupto no lanza excepcion, retorna False (auth_service.py:82-83)."""
        servicio = AuthService()
        assert servicio.verificar_password("cualquier", "hash-no-valido") is False

    def test_decodificar_token_sin_rol_lanza_error(self) -> None:
        """JWT sin claim 'rol' lanza TokenInvalidoError (auth_service.py:119)."""
        sin_rol = jwt.encode(
            {"sub": "x", "exp": int((datetime.now(tz=timezone.utc) + timedelta(hours=1)).timestamp())},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        servicio = AuthService()
        with pytest.raises(TokenInvalidoError):
            servicio.decodificar_token(sin_rol)


class TestRepositorioUsuario:
    def test_obtener_por_id_inexistente_lanza_error(self) -> None:
        """ID que no existe lanza UsuarioNoEncontradoError (usuario_repo.py:116)."""
        repo = RepositorioUsuarioEnMemoria()
        with pytest.raises(UsuarioNoEncontradoError):
            repo.obtener_por_id("id-inexistente-xyz")

    def test_listar_retorna_lista(self) -> None:
        """listar() devuelve la lista actual de usuarios (usuario_repo.py:124-125)."""
        repo = RepositorioUsuarioEnMemoria()
        resultado = repo.listar()
        assert isinstance(resultado, list)
        assert len(resultado) >= 1  # al menos el admin sembrado
