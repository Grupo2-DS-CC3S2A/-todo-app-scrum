"""Servicio de autenticacion JWT y manejo seguro de contrasenas (S2-05).

Responsabilidades:

- Hash de contrasenas con bcrypt (factor configurable; default 12).
- Verificacion constante de contrasena contra hash almacenado.
- Emision y validacion de tokens JWT (HS256) con claims ``sub`` (user_id),
  ``rol`` y ``exp``.
- Registro de usuarios (delegado al ``UsuarioRepository``).
- Seed automatico de un usuario administrador inicial para arranque limpio.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict

import bcrypt
from jose import JWTError, jwt

from src.config import settings
from src.excepciones.errors import (
    CredencialesInvalidasError,
    TokenInvalidoError,
    UsuarioDuplicadoError,
)
from src.logging_config import get_logger
from src.modelos.usuario import (
    LoginInput,
    RegistroInput,
    RolUsuario,
    TokenResponse,
    Usuario,
)
from src.repositorios.usuario_repo import (
    UsuarioRepository,
    get_usuario_repository,
)

logger = get_logger(__name__)


_BCRYPT_MAX_BYTES: int = 72


class AuthService:
    """Coordina autenticacion (login) y gestion de credenciales.

    Usa el modulo ``bcrypt`` directamente (sin passlib) con ``rounds``
    definidos en ``settings.bcrypt_rounds`` (factor 12 por defecto). Las
    contrasenas nunca se almacenan en texto plano: solo el hash bcrypt
    persiste. Las contrasenas se truncan a 72 bytes (limite del algoritmo
    bcrypt) antes de hashear/verificar.
    """

    def __init__(self, repo: UsuarioRepository | None = None) -> None:
        self._repo = repo or get_usuario_repository()
        self._rounds = settings.bcrypt_rounds
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_hours = settings.jwt_expire_hours
        self._seed_admin_si_falta()

    # -------------------------------------------------------------- Hash
    @staticmethod
    def _truncar(password: str) -> bytes:
        return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]

    def hashear_password(self, password: str) -> str:
        """Devuelve el hash bcrypt seguro de una contrasena en claro."""
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(self._truncar(password), salt).decode("utf-8")

    def verificar_password(self, password: str, password_hash: str) -> bool:
        """Compara la contrasena en claro contra el hash almacenado."""
        try:
            return bcrypt.checkpw(
                self._truncar(password),
                password_hash.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------- JWT
    def emitir_token(self, usuario: Usuario) -> TokenResponse:
        """Genera un JWT firmado HS256 con expiracion en horas."""
        ahora = datetime.now(tz=timezone.utc)
        exp = ahora + timedelta(hours=self._expire_hours)
        claims: Dict[str, Any] = {
            "sub": usuario.id,
            "username": usuario.username,
            "rol": usuario.rol.value,
            "iat": int(ahora.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(claims, self._secret, algorithm=self._algorithm)
        return TokenResponse(
            access_token=token,
            expires_in=self._expire_hours * 3600,
        )

    def decodificar_token(self, token: str) -> Dict[str, Any]:
        """Decodifica y valida un JWT.

        Raises:
            TokenInvalidoError: Si el token es invalido o expirado.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except JWTError as exc:
            logger.warning("Token JWT invalido: %s", exc)
            raise TokenInvalidoError(
                "Token de acceso invalido o expirado."
            ) from exc
        if "sub" not in payload or "rol" not in payload:
            raise TokenInvalidoError("Token sin claims requeridos.")
        return payload

    # -------------------------------------------------------------- Login
    def autenticar(self, payload: LoginInput) -> TokenResponse:
        """Valida credenciales y emite JWT.

        Raises:
            CredencialesInvalidasError: Si username no existe o password no coincide.
        """
        try:
            usuario = self._repo.obtener_por_username(payload.username)
        except Exception:
            raise CredencialesInvalidasError(
                "Usuario o contrasena incorrectos."
            )
        if not self.verificar_password(payload.password, usuario.password_hash):
            raise CredencialesInvalidasError(
                "Usuario o contrasena incorrectos."
            )
        logger.info("Login exitoso | username=%s", usuario.username)
        return self.emitir_token(usuario)

    # ------------------------------------------------------------ Registro
    def registrar(self, payload: RegistroInput) -> Usuario:
        """Crea un nuevo usuario con contrasena hasheada.

        Raises:
            UsuarioDuplicadoError: Si el username ya existe.
        """
        if self._repo.existe_username(payload.username):
            raise UsuarioDuplicadoError(
                f"El username '{payload.username}' ya esta registrado."
            )
        usuario = Usuario(
            username=payload.username,
            password_hash=self.hashear_password(payload.password),
            rol=payload.rol,
        )
        return self._repo.guardar(usuario)

    # ----------------------------------------------------- Lookup helpers
    def obtener_usuario(self, usuario_id: str) -> Usuario:
        return self._repo.obtener_por_id(usuario_id)

    # ---------------------------------------------------------- Seed admin
    def _seed_admin_si_falta(self) -> None:
        """Crea un admin inicial si no hay ninguno (idempotente)."""
        if self._repo.existe_username(settings.admin_seed_username):
            return
        try:
            admin = Usuario(
                username=settings.admin_seed_username,
                password_hash=self.hashear_password(
                    settings.admin_seed_password
                ),
                rol=RolUsuario.ADMIN,
            )
            self._repo.guardar(admin)
            logger.info(
                "Admin inicial creado | username=%s",
                settings.admin_seed_username,
            )
        except UsuarioDuplicadoError:
            pass


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    """Provee la instancia singleton del servicio de autenticacion."""
    return AuthService()
