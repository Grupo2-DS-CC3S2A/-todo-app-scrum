# Mesa de Partes Virtual — Arquitectura y Patrones de Diseño

> Documento de referencia técnica del sistema. Cubre la topología desplegada,
> el flujo de cada funcionalidad y el catálogo completo de patrones de diseño
> aplicados, con la ruta exacta del código donde vive cada uno.

---

## 1. Vista general del sistema

Mesa de Partes Virtual permite a un ciudadano validar su identidad (DNI,
dígito de verificación y fecha de emisión), registrar trámites documentarios
dirigidos a dependencias internas y consultar el estado de sus solicitudes.
Un administrador deriva las solicitudes a la dependencia correspondiente con
apoyo de una sugerencia automática de enrutamiento.

### Topología desplegada

| Capa | Tecnología | Despliegue |
|---|---|---|
| Frontend | React + Vite + TypeScript | Vercel — `mdp-frontend-*.vercel.app` |
| Backend | FastAPI (Python 3.10+) | Google Cloud Run — servicio `todo-app-backend`, proyecto `mesa-de-partes-501300`, `us-central1` |
| Base de datos | PostgreSQL (Supabase) | Supabase Cloud — tablas `citizens`, `solicitudes`, `dependencias`, `usuarios` |
| CI/CD | GitHub Actions | `ci.yml` (lint + tipos + tests + cobertura ≥85%), `docker-ci.yml` (deploy a Cloud Run + `supabase db push`) |

El frontend lee `VITE_API_BASE_URL` para hablar con el backend; el backend
usa `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (service role: la tabla
`citizens` tiene RLS activo sin políticas, de modo que **solo** el backend
puede leerla — nunca el navegador).

### Estructura del backend (capas)

```
backend/src/
├── main.py               # Application Factory: compone la app FastAPI
├── config.py             # Settings inmutables desde variables de entorno
├── logging_config.py     # Logging estructurado centralizado
├── excepciones/          # Errores de dominio + handlers HTTP
├── modelos/              # Entidades y DTOs Pydantic (invariantes de dominio)
├── repositorios/         # Puertos + adaptadores de persistencia
├── rutas/                # Capa HTTP (routers FastAPI)
├── servicios/            # Lógica de dominio y orquestación
└── utilidades/           # Motor genético, cifrado
```

Regla de dependencia: `rutas → servicios → repositorios → modelos`.
Ninguna capa inferior conoce a la superior.

---

## 2. Flujos funcionales

### 2.1 Validación de ciudadano (`POST /api/validate`)

1. El frontend envía `{dni, digit, date}`.
2. `rutas/validacion.py` delega en `CiudadanoService`.
3. El servicio consulta el puerto `CiudadanoRepository`; en producción la
   petición pasa por el **Proxy de caché** y llega al adaptador Supabase,
   que busca coincidencia exacta en `public.citizens`.
4. Si coincide → `{valid: true, dni, firstname, lastname}`; si no →
   `{valid: false}` (el mensaje "los datos no coinciden" del frontend).

### 2.2 Derivación de solicitud (`POST /api/admin/solicitudes/derivar`)

1. `verificar_admin` autoriza (JWT Bearer con rol admin, o token legacy).
2. La ruta invoca la **Fachada** `MesaDePartesFacade.derivar(payload)`.
3. Dentro del subsistema:
   - `DocumentoFactory` (**Factory Method**) valida el documento según el
     tipo de persona (DNI 8 dígitos / RUC 11 dígitos).
   - Se calcula `fecha_maxima_respuesta` = 30 días hábiles.
   - La **Cadena de Aprobación** (Chain of Responsibility) procesa la
     solicitud: validación de ciudadano → aprobación legal → derivación.
     Si Asesoría Legal rechaza (detalle < 15 caracteres), el resultado es
     la solicitud en estado `Rechazada legal`.
   - El repositorio persiste el resultado real (decorado con auditoría).
   - El **Bridge de notificaciones** informa al ciudadano el resultado
     (derivación o rechazo) por el canal configurado.
4. La ruta devuelve el DTO `SolicitudDerivada`.

### 2.3 Sugerencia de dependencia (`POST /api/admin/solicitudes/sugerir-dependencia`)

La fachada delega en `SugerenciaDependenciaService`, que ejecuta la
**Strategy** configurada (motor genético o reglas deterministas) y devuelve
`{dependencia, puntaje}`. No persiste nada: el admin decide.

### 2.4 Autenticación (`/api/auth/*`)

Login con bcrypt (factor 12) + emisión de JWT HS256 con claims `sub`, `rol`,
`exp`. Seed idempotente de un admin inicial al arrancar.

---

## 3. Catálogo de patrones de diseño

### 3.1 Creacionales

#### Factory Method — `backend/src/modelos/documento_solicitante.py`

**Problema**: la solicitud debe acompañarse de un documento distinto según
el tipo de persona (Natural → DNI, Jurídica → RUC), cada uno con su propia
regla de formato.

**Solución**: `DocumentoFactory.crear(tipo, numero)` decide qué clase
instanciar (`SolicitudPersonaNatural` / `SolicitudPersonaJuridica`); la
validación de formato vive en cada subtipo vía Pydantic. Agregar un nuevo
tipo de documento = nueva subclase + una rama en la fábrica, sin tocar a
los consumidores.

#### Singleton (vía `functools.lru_cache`) — providers `get_*`

`get_solicitud_service`, `get_auth_service`, `get_solicitud_repository`,
`get_ciudadano_service`, `get_sugerencia_dependencia_service` usan
`@lru_cache(maxsize=1)`: una única instancia por proceso, sin estado global
mutable ni metaclases. Los tests lo anulan con `cache_clear()` +
`dependency_overrides`.

### 3.2 Estructurales

#### Facade — `backend/src/servicios/mesa_de_partes_facade.py`

**Problema**: las rutas administrativas importaban y coordinaban tres
servicios distintos (solicitudes, sugerencias, y a futuro notificaciones);
la orquestación estaba dispersa en la capa HTTP.

**Solución**: `MesaDePartesFacade` expone las cuatro operaciones que la
capa HTTP necesita (`sugerir`, `derivar`, `obtener`, `listar`) y esconde
la coordinación (incluida la notificación post-derivación). Las rutas
dependen de **una** abstracción. El provider resuelve los servicios vía
`Depends`, así los overrides de los tests siguen funcionando.

#### Decorator — `backend/src/repositorios/solicitud_repo_auditoria.py`

**Problema**: cada adaptador de persistencia (en memoria, Supabase)
duplicaba su propio `logger.info` dentro de `guardar()` — persistencia y
auditoría mezcladas.

**Solución**: `RepositorioSolicitudConAuditoria` implementa el mismo puerto
`SolicitudRepository`, envuelve cualquier adaptador y registra la auditoría
(id, dependencia, estado, duración en ms) por fuera. Los adaptadores quedan
puros. La composición ocurre solo en el borde:
`get_solicitud_repository() → Auditoria(Supabase())`.

#### Proxy — `backend/src/repositorios/ciudadano_repo.py`

**Problema**: cada validación de DNI viaja a Supabase; validaciones
repetidas (reintentos del mismo ciudadano) pagan la latencia completa.

**Solución**: `CiudadanoRepositoryCacheProxy` implementa el puerto
`CiudadanoRepository` y controla el acceso al adaptador remoto: aciertos
se sirven desde memoria durante un TTL (300 s); los fallos **no** se
cachean (un ciudadano recién sembrado valida de inmediato). Incluye purga
de expirados y desalojo FIFO al llegar a capacidad.

**Decorator vs Proxy** (distinción para la exposición): el Decorator
*agrega una responsabilidad* (auditar) sin cambiar la semántica de la
operación; el Proxy *controla el acceso* al objeto real (decide si la
llamada viaja o no).

#### Bridge — `backend/src/servicios/notificaciones.py`

**Problema**: el formulario ya captura correo y celular del ciudadano; se
necesita notificar distintos eventos (derivación, rechazo legal) por
distintos medios (log/consola, email, SMS). Subclasificar cada combinación
explota en N×M clases.

**Solución**: dos jerarquías independientes unidas por composición —
`NotificadorSolicitud` (qué se dice: `NotificacionDerivacion`,
`NotificacionRechazoLegal`) × `CanalNotificacion` (cómo se envía:
`CanalConsola`, `CanalEmail`, `CanalSMS`). Agregar un canal no toca los
tipos de notificación y viceversa. Email y SMS son stubs deliberados: el
formato del mensaje ya es el final; integrar SMTP/proveedor SMS solo
reemplaza el canal.

#### Adapter — `backend/src/repositorios/solicitud_repo.py` y `ciudadano_repo.py`

Los adaptadores `RepositorioSolicitudSupabase` / `RepositorioSolicitudEnMemoria`
(y `CiudadanoRepositorySupabase`) traducen el contrato del dominio
(`SolicitudRepository`, `CiudadanoRepository`) a la API concreta de cada
tecnología (cliente PostgREST de Supabase, diccionario en memoria). El
servicio no distingue cuál usa (DIP): en tests se inyecta el de memoria sin
credenciales; en producción, el de Supabase.

### 3.3 De comportamiento

#### Chain of Responsibility — `backend/src/servicios/cadena_aprobacion.py` (MDP-07)

**Problema**: aprobar una solicitud exige verificaciones sucesivas e
independientes (identidad del ciudadano → marco legal → dependencia
destino), y cualquiera puede cortar el flujo.

**Solución**: `ManejadorAprobacion` define el eslabón; `set_siguiente()`
encadena con interfaz fluida. `AprobacionLegalHandler` corta la cadena
devolviendo la solicitud en `Rechazada legal`; los demás delegan con
`super().manejar()`. La construcción de la cadena está centralizada en
`_construir_cadena_aprobacion()` (`solicitud_service.py`): `derivar()` no
conoce los eslabones concretos ni su orden.

#### Strategy — `backend/src/servicios/enrutamiento_service.py` (MDP-10)

**Problema**: el puntaje de prioridad de una sugerencia de enrutamiento
puede calcularse de formas distintas (motor genético con variabilidad, o
reglas deterministas de respaldo) y debe poder cambiarse sin tocar al
consumidor.

**Solución**: `EstrategiaEnrutamiento` (interfaz) con dos estrategias
intercambiables: `EnrutamientoGenetico` (usa `AlgoritmoGenetico` de
`utilidades/`) y `EnrutamientoReglas` (fallback determinista, usado también
en tests). `SugerenciaDependenciaService` recibe la estrategia por
inyección.

### 3.4 Patrones de arquitectura (no GoF, pero presentes)

| Patrón | Dónde | Qué aporta |
|---|---|---|
| Repository (puerto/adaptador) | `repositorios/*` | Persistencia intercambiable; tests sin credenciales |
| Dependency Injection | FastAPI `Depends` en todas las rutas | Bajo acoplamiento; overrides en tests |
| Application Factory | `main.create_app()` | Composición de la app en un solo punto |
| DTO / Entidad separados | `modelos/*` (`DerivacionInput` vs `Solicitud` vs `SolicitudDerivada`) | El contrato HTTP no expone la entidad de dominio |

### 3.5 Patrones evaluados y descartados (decisión consciente)

- **Composite**: aplicaría a expedientes con documentos anexos jerárquicos;
  esa funcionalidad no existe todavía. Aplicarlo hoy sería sobre-ingeniería.
  Se reevaluará si se implementan adjuntos/expedientes compuestos.
- **Flyweight**: pensado para miles de objetos con estado intrínseco
  compartido; los catálogos del sistema (7 dependencias, 6 estados) son
  enums triviales. No hay problema de memoria que resolver.

> Criterio aplicado: un patrón se incorpora cuando resuelve un problema
> real y presente del código, no para engordar el catálogo.

---

## 4. Calidad y verificación

- CI (`.github/workflows/ci.yml`): `black --check`, `flake8`, `mypy`
  (plugin Pydantic), `pytest --cov=src --cov-fail-under=85`.
- Estado tras la refactorización estructural: **151 tests, cobertura 92%**.
- Tests específicos de patrones:
  - `tests/test_mesa_de_partes_facade.py` (Facade + integración con Bridge)
  - `tests/test_solicitud_repo_auditoria.py` (Decorator)
  - `tests/test_ciudadano_cache_proxy.py` (Proxy: TTL, no-cacheo de fallos, desalojo)
  - `tests/test_notificaciones.py` (Bridge: mismo notificador × 3 canales)
  - `tests/test_cadena_aprobacion.py`, `tests/test_enrutamiento_service.py`,
    `tests/test_documento_factory.py` (patrones previos)

## 5. Datos de prueba

La migración `supabase/migrations/20261782604800_mdp_54_initial_schema.sql`
siembra la tabla `citizens`. Credenciales válidas para demo:

| DNI | Dígito | Fecha de emisión | Ciudadano |
|---|---|---|---|
| 40392536 | 1 | 2024-07-25 | CESAR LOPEZ ARTEAGA |
| 81000001 | 4 | 2022-01-14 | MATEO SALAZAR PAREDES |
| 81000002 | 7 | 2021-03-09 | LUCIA RAMIREZ TORRES |
| 81000003 | 2 | 2020-05-18 | DIEGO QUISPE HUAMAN |
| 81000004 | 9 | 2023-07-22 | VALERIA CASTRO MENDOZA |
