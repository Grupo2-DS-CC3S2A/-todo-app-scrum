# SGSI - Controles de Seguridad implementados

> Evidencia documentada para las historias de Controles
> Tecnológicos y Organizacionales con el
> Formato: control -> estado -> evidencia (ruta exacta) -> fecha
> Evidencia documentada + responsable + validación en una futura auditoria.

## Proteger la información usada en pruebas

**Evidencia**: `backend/tests/conftest.py` (`usar_repo_en_memoria_para_tests`)
sustituye todos los repositorios respaldados por Supabase por adaptadores en
memoria (`RepositorioUsuarioEnMemoria`, `RepositorioSolicitudEnMemoria`)
antes de que corra cualquier test. Los 177 tests del backend (151 originales
+ 26 del ciclo de vida de accesos, ver más abajo) usan exclusivamente datos
ficticios generados en el propio test - ninguno requiere ni toca credenciales
reales de Supabase. `pytest.ini` fija `testpaths = tests`, por lo que ningún
test de producción se ejecuta contra datos reales por accidente.

## Aplicar principios de arquitectura de sistemas seguros

**Evidencia**: `docs/arquitectura-y-patrones.md` - regla de dependencia
`rutas -> servicios -> repositorios -> modelos` (backend), separación
puerto/adaptador para persistencia (Repository), y el catálogo de patrones
de las secciones 3.1–3.6 (incluye ahora `firma-java`). La separación de
llave privada/pública en tres bases lógicas (§"Tres bases lógicas para la
firma digital") es en sí misma un control de seguridad arquitectónico.

## Gestión de cambios formal

**Evidencia**: `.github/workflows/ci.yml` bloquea el merge de cualquier
cambio a `backend/` que no pase `black --check`, `flake8`, `mypy` y
`pytest --cov=src --cov-fail-under=85`. Todo cambio llega vía Pull Request
(no hay push directo documentado a `main`/`developer` en el flujo del
equipo).

## Ciclo de vida de identidades digitales y control de acceso

**Qué cambió**: antes solo existía alta de usuarios (`POST /api/auth/register`).
Se agregó el resto del ciclo de vida:

| Endpoint | Rol requerido | Qué hace |
|---|---|---|
| `GET /api/auth/usuarios` | admin | Revisión de accesos: lista usuarios con `rol` y `activo` |
| `PATCH /api/auth/usuarios/{id}/estado` | admin | Activa o revoca el acceso de un usuario |
| `PATCH /api/auth/usuarios/{id}/rol` | admin | Cambia el rol asignado |

**Evidencia de código**: `backend/src/modelos/usuario.py` (campo `activo`),
`backend/src/servicios/auth_service.py` (`listar_usuarios`,
`actualizar_estado`, `actualizar_rol`), `backend/src/rutas/auth.py`,
`backend/src/repositorios/usuario_repo.py` (método `actualizar` en ambos
adaptadores), migración `supabase/migrations/20261782605100_usuarios_activo.sql`.

**Garantías verificadas** (tests en `backend/tests/test_auth.py::TestCicloDeVidaDeAccesos`,
además probadas en vivo contra un backend + Supabase local reales):

- Revocar el acceso bloquea logins futuros (`UsuarioInactivoError`, 403).
- Revocar el acceso invalida de inmediato cualquier JWT ya emitido - no hay
  que esperar a que expire (`auth_deps.get_current_user` re-verifica
  `activo` en cada request).
- Un administrador no puede desactivar su propia cuenta (evita quedar sin
  ningún admin con sesión válida).
- Solo `admin` puede listar usuarios, revocar accesos o cambiar roles
  (403 para cualquier otro rol).

## Registrar y proteger logs de actividades y accesos denegados

**Evidencia**:

- `backend/src/excepciones/errors.py` registra
  automáticamente (`logger.warning`) *todo* `DominioVotacionError` no
  capturado explícitamente - esto ya cubre credenciales inválidas, tokens
  inválidos/expirados y accesos denegados (403) en cualquier endpoint, sin
  que cada ruta tenga que loguearlo a mano.
- `auth_service.py` agrega logging estructurado específico para
  eventos de control de acceso que el handler genérico no puede describir
  con contexto suficiente: intento de login contra una cuenta desactivada
  (`Login rechazado, cuenta inactiva | username=...`), revocación/activación
  de acceso (`Acceso revocado | id=... | username=... | por=...`) y cambio
  de rol (`Rol actualizado | id=... | username=... | rol=...`) - quedando
  registrado *quién* ejecutó la acción sobre *quién*.