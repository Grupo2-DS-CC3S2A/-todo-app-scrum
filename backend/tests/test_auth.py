"""Tests de Autenticacion JWT y control de sesion.

Cubre los criterios de aceptacion:

- Contrasenas nunca se almacenan en texto plano (verificable via repo).
- Tokens expiran en 24h (claim ``exp`` ~24h despues de ``iat``).
- Endpoints protegidos rechazan acceso no autorizado.

Casos exigidos por la tarjeta:

- Login exitoso (200 + JWT).
- Login fallido por credenciales invalidas (401).
- Acceso sin token (401).
- Acceso con token expirado (401).
- Acceso sin permisos suficientes (403).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.config import settings
from src.main import app
from src.modelos.usuario import RolUsuario
from src.repositorios.usuario_repo import RepositorioUsuarioEnMemoria
from src.servicios.auth_service import get_auth_service

URL_LOGIN = "/api/auth/login"
URL_REGISTER = "/api/auth/register"
URL_ME = "/api/auth/me"
URL_USUARIOS = "/api/auth/usuarios"
URL_ADMIN_LIST = "/api/admin/solicitudes"


def _estado_url(usuario_id: str) -> str:
    return f"{URL_USUARIOS}/{usuario_id}/estado"


def _rol_url(usuario_id: str) -> str:
    return f"{URL_USUARIOS}/{usuario_id}/rol"


ADMIN_USERNAME = settings.admin_seed_username
ADMIN_PASSWORD = settings.admin_seed_password


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_usuarios_y_reseedea():
    """Limpia el repositorio singleton y vuelve a sembrar el admin."""
    repo = RepositorioUsuarioEnMemoria()
    with repo._lock:
        repo._por_id.clear()
        repo._por_username.clear()
    auth = get_auth_service()
    auth._seed_admin_si_falta()
    yield


def _login(client: TestClient, username: str, password: str):
    return client.post(URL_LOGIN, json={"username": username, "password": password})


def _token_admin(client: TestClient) -> str:
    resp = _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- Login
class TestLogin:
    def test_login_exitoso_devuelve_jwt(self, client: TestClient) -> None:
        resp = _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == settings.jwt_expire_hours * 3600
        assert isinstance(body["access_token"], str) and body["access_token"]

    def test_login_credenciales_invalidas_devuelve_401(
        self, client: TestClient
    ) -> None:
        resp = _login(client, ADMIN_USERNAME, "password-incorrecto-999")
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "CredencialesInvalidasError"

    def test_login_usuario_inexistente_devuelve_401(self, client: TestClient) -> None:
        resp = _login(client, "no-existe-jamas", "Password123!")
        assert resp.status_code == 401

    def test_token_contiene_claims_requeridos_y_exp_24h(
        self, client: TestClient
    ) -> None:
        token = _token_admin(client)
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["rol"] == RolUsuario.ADMIN.value
        assert "sub" in payload and "exp" in payload and "iat" in payload
        delta = payload["exp"] - payload["iat"]
        assert delta == settings.jwt_expire_hours * 3600


# ------------------------------------------------------------ Password hash
class TestPasswordHash:
    def test_password_nunca_se_almacena_en_texto_plano(self) -> None:
        repo = RepositorioUsuarioEnMemoria()
        admin = repo.obtener_por_username(ADMIN_USERNAME)
        assert admin.password_hash != ADMIN_PASSWORD
        assert admin.password_hash.startswith("$2")  # bcrypt prefix


# ---------------------------------------------------------------- /me
class TestMe:
    def test_me_sin_token_devuelve_401(self, client: TestClient) -> None:
        resp = client.get(URL_ME)
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "TokenInvalidoError"

    def test_me_con_token_valido_devuelve_usuario(self, client: TestClient) -> None:
        token = _token_admin(client)
        resp = client.get(URL_ME, headers=_auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == ADMIN_USERNAME
        assert body["rol"] == RolUsuario.ADMIN.value

    def test_me_con_token_expirado_devuelve_401(self, client: TestClient) -> None:
        ahora = datetime.now(tz=timezone.utc)
        expirado = jwt.encode(
            {
                "sub": "fake-id",
                "rol": RolUsuario.ADMIN.value,
                "iat": int((ahora - timedelta(hours=48)).timestamp()),
                "exp": int((ahora - timedelta(hours=1)).timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        resp = client.get(URL_ME, headers=_auth_header(expirado))
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "TokenInvalidoError"

    def test_me_con_token_firmado_con_secret_distinto_devuelve_401(
        self, client: TestClient
    ) -> None:
        falso = jwt.encode(
            {"sub": "x", "rol": "admin", "exp": 9999999999},
            "secret-incorrecto",
            algorithm=settings.jwt_algorithm,
        )
        resp = client.get(URL_ME, headers=_auth_header(falso))
        assert resp.status_code == 401


# ------------------------------------------------------------- Register
class TestRegister:
    def _registrar(self, client: TestClient, token: str, **overrides):
        payload = {
            "username": "operador01",
            "password": "Operador123!",
            "rol": "operador",
        }
        payload.update(overrides)
        return client.post(URL_REGISTER, json=payload, headers=_auth_header(token))

    def test_register_sin_token_devuelve_401(self, client: TestClient) -> None:
        resp = client.post(
            URL_REGISTER,
            json={
                "username": "nuevo",
                "password": "Password123!",
                "rol": "operador",
            },
        )
        assert resp.status_code == 401

    def test_register_con_admin_crea_usuario(self, client: TestClient) -> None:
        token = _token_admin(client)
        resp = self._registrar(client, token)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["username"] == "operador01"
        assert body["rol"] == RolUsuario.OPERADOR.value

    def test_register_con_rol_no_admin_devuelve_403(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        # crea un operador
        self._registrar(client, admin_token).raise_for_status()
        # login del operador
        op_resp = _login(client, "operador01", "Operador123!")
        assert op_resp.status_code == 200
        op_token = op_resp.json()["access_token"]
        # operador intenta registrar otro usuario
        resp = self._registrar(
            client,
            op_token,
            username="otro01",
            password="Password123!",
        )
        assert resp.status_code == 403
        assert resp.json()["tipo"] == "PermisoDenegadoError"

    def test_register_username_duplicado_devuelve_409(self, client: TestClient) -> None:
        token = _token_admin(client)
        assert self._registrar(client, token).status_code == 201
        dup = self._registrar(client, token)
        assert dup.status_code == 409
        assert dup.json()["tipo"] == "UsuarioDuplicadoError"


# ---------------------------------------------- Endpoints admin protegidos
class TestAdminProtegidoConJWT:
    def test_admin_endpoint_con_jwt_admin_devuelve_200(
        self, client: TestClient
    ) -> None:
        token = _token_admin(client)
        resp = client.get(URL_ADMIN_LIST, headers=_auth_header(token))
        assert resp.status_code == 200

    def test_admin_endpoint_con_jwt_no_admin_devuelve_403(
        self, client: TestClient
    ) -> None:
        admin_token = _token_admin(client)
        client.post(
            URL_REGISTER,
            json={
                "username": "operador02",
                "password": "Operador123!",
                "rol": "operador",
            },
            headers=_auth_header(admin_token),
        ).raise_for_status()
        op_token = _login(client, "operador02", "Operador123!").json()["access_token"]
        resp = client.get(URL_ADMIN_LIST, headers=_auth_header(op_token))
        assert resp.status_code == 403
        assert resp.json()["tipo"] == "NoAutorizadoError"

    def test_admin_endpoint_con_jwt_expirado_devuelve_403(
        self, client: TestClient
    ) -> None:
        ahora = datetime.now(tz=timezone.utc)
        expirado = jwt.encode(
            {
                "sub": "x",
                "rol": RolUsuario.ADMIN.value,
                "iat": int((ahora - timedelta(hours=48)).timestamp()),
                "exp": int((ahora - timedelta(hours=1)).timestamp()),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        resp = client.get(URL_ADMIN_LIST, headers=_auth_header(expirado))
        assert resp.status_code == 403
        assert resp.json()["tipo"] == "NoAutorizadoError"

    def test_admin_endpoint_x_admin_token_legacy_aun_funciona(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            URL_ADMIN_LIST,
            headers={"X-Admin-Token": "RENIEC_ADMIN_SUPER_SECRET_2026"},
        )
        assert resp.status_code == 200


# Ciclo de vida de accesos
class TestCicloDeVidaDeAccesos:
    def _crear_operador(
        self, client: TestClient, admin_token: str, username: str = "operador01"
    ) -> str:
        resp = client.post(
            URL_REGISTER,
            json={"username": username, "password": "Operador123!", "rol": "operador"},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def test_listar_usuarios_sin_admin_devuelve_403(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        self._crear_operador(client, admin_token)
        op_token = _login(client, "operador01", "Operador123!").json()["access_token"]
        resp = client.get(URL_USUARIOS, headers=_auth_header(op_token))
        assert resp.status_code == 403

    def test_listar_usuarios_incluye_estado_activo(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        self._crear_operador(client, admin_token)
        resp = client.get(URL_USUARIOS, headers=_auth_header(admin_token))
        assert resp.status_code == 200
        usernames_activos = {u["username"]: u["activo"] for u in resp.json()}
        assert usernames_activos["operador01"] is True

    def test_desactivar_usuario_bloquea_login_futuro(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        operador_id = self._crear_operador(client, admin_token)

        resp = client.patch(
            _estado_url(operador_id),
            json={"activo": False},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["activo"] is False

        login_resp = _login(client, "operador01", "Operador123!")
        assert login_resp.status_code == 403
        assert login_resp.json()["tipo"] == "UsuarioInactivoError"

    def test_desactivar_usuario_revoca_token_ya_emitido(
        self, client: TestClient
    ) -> None:
        admin_token = _token_admin(client)
        operador_id = self._crear_operador(client, admin_token)
        op_token = _login(client, "operador01", "Operador123!").json()["access_token"]

        # El token todavia es valido antes de la revocacion.
        assert client.get(URL_ME, headers=_auth_header(op_token)).status_code == 200

        client.patch(
            _estado_url(operador_id),
            json={"activo": False},
            headers=_auth_header(admin_token),
        ).raise_for_status()

        resp = client.get(URL_ME, headers=_auth_header(op_token))
        assert resp.status_code == 401
        assert resp.json()["tipo"] == "TokenInvalidoError"

    def test_reactivar_usuario_permite_login_de_nuevo(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        operador_id = self._crear_operador(client, admin_token)
        client.patch(
            _estado_url(operador_id),
            json={"activo": False},
            headers=_auth_header(admin_token),
        ).raise_for_status()

        resp = client.patch(
            _estado_url(operador_id),
            json={"activo": True},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["activo"] is True
        assert _login(client, "operador01", "Operador123!").status_code == 200

    def test_admin_no_puede_desactivar_su_propia_cuenta(
        self, client: TestClient
    ) -> None:
        admin_token = _token_admin(client)
        me_resp = client.get(URL_ME, headers=_auth_header(admin_token))
        admin_id = me_resp.json()["id"]

        resp = client.patch(
            _estado_url(admin_id),
            json={"activo": False},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 403
        assert resp.json()["tipo"] == "PermisoDenegadoError"

    def test_actualizar_estado_usuario_inexistente_devuelve_404(
        self, client: TestClient
    ) -> None:
        admin_token = _token_admin(client)
        resp = client.patch(
            _estado_url("no-existe"),
            json={"activo": False},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 404

    def test_cambiar_rol_actualiza_permisos_en_el_siguiente_token(
        self, client: TestClient
    ) -> None:
        admin_token = _token_admin(client)
        operador_id = self._crear_operador(client, admin_token)

        resp = client.patch(
            _rol_url(operador_id),
            json={"rol": "admin"},
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rol"] == "admin"

        nuevo_token = _login(client, "operador01", "Operador123!").json()[
            "access_token"
        ]
        resp = client.get(URL_ADMIN_LIST, headers=_auth_header(nuevo_token))
        assert resp.status_code == 200

    def test_cambiar_rol_sin_admin_devuelve_403(self, client: TestClient) -> None:
        admin_token = _token_admin(client)
        operador_id = self._crear_operador(client, admin_token)
        op_token = _login(client, "operador01", "Operador123!").json()["access_token"]

        resp = client.patch(
            _rol_url(operador_id),
            json={"rol": "admin"},
            headers=_auth_header(op_token),
        )
        assert resp.status_code == 403
