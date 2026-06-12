# SCRUM-21 - Especificación de Flujos de Sesión, Expiración de Tokens y Manejo de Roles

**Historia padre:** SCRUM-11 HU01 - Registro e inicio de sesión
**Tipo:** [BA] Especificación de negocio
**Estado:** Finalizado

---

## Objetivo

Definir las reglas de negocio del sistema de autenticación JWT para que cada
rol acceda exclusivamente a los recursos que le corresponden, y que la sesión
expire y se rechace de forma predecible.

---

## Reglas de Negocio

**Sesion**
- El login valida credenciales contra hash bcrypt y emite un JWT HS256 con
duración de 24 horas (configurable vía `JWT_EXPIRE_HOURS`).
- Las contraseñas nunca se almacenan en texto plano.
- El logout es del lado del cliente: limpia `localStorage`. No existe
invalidación del token en el servidor.

**Expiración**
- Un token expirado es rechazado con **401** en rutas de autenticación
(`/api/auth/*`) y con **403** en rutas de administración (`/api/admin/*`).
- El frontend detecta la expiración en `localStorage` antes de llamar al
backend y redirige al login sin petición adicional.

**Roles y permisos**

| Endpoint | Sin auth | Ciudadano / Operador | Admin |
|---|---|---|---|
| `POST /api/auth/login` | OK | - | - |
| `GET /api/auth/me` | 401 | OK | OK |
| `POST /api/auth/register` | 401 | 403 | OK |
| `GET /api/admin/solicitudes*` | 403 | 403 | OK |
| `POST /api/admin/solicitudes/derivar` | 403 | 403 | OK |

---

## Criterios de Aceptación

Cada criterio esta cubierto por al menos un test existente en la suite.

| CA | Regla | Test que lo verifica |
|---|---|---|
| CA-01 | Login exitoso emite JWT con claims `sub`, `rol` y `exp` | `test_auth.py::TestLogin::test_login_exitoso_devuelve_jwt` |
| CA-02 | Credenciales inválidas devuelven 401 sin revelar si el usuario existe | `test_scrum25.py::TestLogin::test_login_password_incorrecta_devuelve_401` |
| CA-03 | Token expirado en `/api/auth/me` devuelve 401 | `test_auth.py::TestMe::test_me_con_token_expirado_devuelve_401` |
| CA-04 | Token expirado en endpoints admin devuelve 403 | `test_auth.py::TestAdminProtegidoConJWT::test_admin_endpoint_con_jwt_expirado_devuelve_403` |
| CA-05 | Petición sin token devuelve 401 en rutas de autenticación | `test_scrum25.py::TestDenegacionAccesos::test_me_sin_token_devuelve_401` |
| CA-06 | Rol insuficiente devuelve 403 | `test_auth.py::TestRegister::test_register_con_rol_no_admin_devuelve_403` |
| CA-07 | Contraseñas almacenadas como hash bcrypt (prefijo `$2`) | `test_auth.py::TestPasswordHash::test_password_nunca_se_almacena_en_texto_plano` |