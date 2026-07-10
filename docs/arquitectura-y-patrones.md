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
apoyo de una sugerencia automática de enrutamiento. Adicionalmente, el
ciudadano puede firmar digitalmente el documento de su trámite: el frontend
llama directamente a un subsistema Java independiente (`firma-java/`) que
genera el par de llaves RSA, firma el archivo y devuelve un contenedor
verificable.

### Topología desplegada

| Capa | Tecnología | Despliegue |
|---|---|---|
| Frontend | React + Vite + TypeScript | Vercel — `mdp-frontend-*.vercel.app` |
| Backend | FastAPI (Python 3.10+) | Google Cloud Run — servicio `todo-app-backend`, proyecto `mesa-de-partes-501300`, `us-central1` |
| Firma digital | Java 21 + Spring Boot 3.3.5 (`identity-key-service` puerto 8082, `signature-service` puerto 8083) | Solo local (`mvn spring-boot:run` por módulo) — sin CI ni despliegue automatizado todavía |
| Base de datos | PostgreSQL (Supabase) | Supabase Cloud — schema `public` (`citizens`, `solicitudes`, `dependencias`, `usuarios`), schema `firma_publica` (llaves públicas), schema `tramite_documentario` (`documentos_tramitados`) |
| CI/CD | GitHub Actions | `ci.yml` (lint + tipos + tests + cobertura ≥85%, solo `backend/`), `docker-ci.yml` (deploy a Cloud Run + `supabase db push`) |

El frontend lee `VITE_API_BASE_URL` para hablar con el backend FastAPI, y
`VITE_SIGNATURE_API_URL` (por defecto `http://localhost:8083`, no listada en
`frontend/.env.example`) para hablar **directamente** con `signature-service`
— la firma digital no pasa por el backend Python. El backend usa
`SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (service role: la tabla
`citizens` tiene RLS activo sin políticas, de modo que **solo** el backend
puede leerla — nunca el navegador).

### Tres bases lógicas para la firma digital

La migración `20261782604900_firma_digital_keys.sql` separa intencionalmente
la llave privada de la pública:

1. **Base 1** (privada) — `public.citizens.llave_privada`, en el mismo
   Supabase del backend. Solo `identity-key-service` la lee (vía JDBC directo,
   no PostgREST), y solo se la entrega a `signature-service` con un
   `X-Internal-Token` compartido.
2. **Base 2** (pública) — schema `firma_publica.citizens`, con
   `llave_publica`. Se usa para verificar firmas sin exponer nunca la llave
   privada.
3. **Base 3** (documentos firmados) — H2 embebido de `signature-service`
   (`SIGNED_DB_URL`, archivo local), con el documento, el hash, la firma y el
   log de auditoría de cada operación de firma/verificación.

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

### Estructura de firma-java (microservicios)

```
firma-java/
├── common-crypto/          # librería compartida: hashing SHA-256, firma/verificación RSA, generación de llaves
├── identity-key-service/   # :8082 — dueño de la llave privada y la pública; API interna
│   └── src/main/java/pe/edu/uni/firma/identity/
│       ├── controller/      # IdentityController — /api/personas/*
│       ├── service/         # IdentityKeyService, SeedCitizenFactory
│       └── repository/      # Public/PrivateCitizenKeyRepository (JDBC directo a Supabase)
└── signature-service/      # :8083 — firma, almacena y verifica documentos
    └── src/main/java/pe/edu/uni/firma/signature/
        ├── controller/      # DocumentController — /api/documentos/*
        ├── service/         # DocumentSignatureFacade, DocumentSignatureEmailService
        ├── client/          # IdentityKeyClient — llama a identity-key-service con X-Internal-Token
        ├── patterns/        # Command, Strategy, Registry (ver §3.5)
        ├── container/       # empaquetado del documento firmado (.uni-signed)
        └── repository/      # SignedDocumentRepository, AuditRepository (H2 local)
```

`signature-service` nunca lee ni escribe la llave privada directamente:
siempre la pide a `identity-key-service` por HTTP, autenticado con
`INTERNAL_SERVICE_TOKEN`. Los dos módulos comparten `common-crypto` como
dependencia Maven, no por copia de código.

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

### 2.5 Registro y consulta de trámite (`/api/tramites/*`)

`rutas/tramites.py` habla directo con Supabase
(`client.schema("tramite_documentario")`) para el alta (`POST /`), el
listado por DNI (`GET /{dni}`) y la búsqueda por tipo de documento + rango
de fechas (`GET /{dni}/buscar`) — estos tres endpoints todavía no pasan por
`servicios/` ni `repositorios/` (deuda técnica preexistente, no resuelta por
completo). El endpoint de reemplazo (`PATCH /{tramite_id}/reemplazo`, ver
2.7) sí usa `DocumentoTramitadoRepository` desde `repositorios/`, así que el
archivo hoy mezcla ambos estilos. **Ya tiene tests** en
`tests/test_tramites.py` (antes no existía), usando un cliente Supabase
falso duck-typed porque las tres rutas originales no tienen un punto de
inyección de dependencias.

`TramiteResponse` incluye `motivo_rechazo` y `fecha_resolucion` (nulos hasta
que un operador resuelve el trámite — ver 2.7).

### 2.6 Firma digital de documento (`signature-service`, fuera del backend Python)

1. El frontend llama `POST http://localhost:8083/api/documentos/sign`
   (multipart: `dni`, `file`, `email`, `dependencia`, `documentType`) —
   `frontend/src/api/signatureApi.ts`, sin pasar por el backend FastAPI.
2. `DocumentController` arma un `SignDocumentCommand` (**Command**) y lo
   pasa a la **Fachada** `DocumentSignatureFacade`.
3. La fachada pide la llave privada y pública del DNI a
   `identity-key-service` (`IdentityKeyClient`, HTTP + `X-Internal-Token`).
4. Un `DocumentPreprocessor` (**Strategy**, elegido por tipo de contenido vía
   `DocumentPreprocessorRegistry`) prepara el archivo — si es PDF, le agrega
   un sello visible.
5. `OriginalCryptoAdapter` calcula el hash SHA-256 y firma con RSA modular
   original (protocolo propio de la cátedra, no PKCS estándar).
6. `SignedEnvelopeFactory` empaqueta documento + hash + firma + certificado
   lógico en un único contenedor `.uni-signed` (formato ZIP propio), que se
   guarda en la Base 3 (H2 local) junto a un registro de auditoría.
7. Si se envió `email`, `DocumentSignatureEmailService` notifica al
   ciudadano por SMTP con el documento visible adjunto.
8. Verificación (`POST /api/documentos/{id}/verify` o
   `/verify-upload`): recalcula el hash, valida la firma con
   `RsaModularVerificationStrategy` y confirma que el certificado embebido
   coincide con la Base 2 (`identity-key-service`) — un documento solo es
   válido si las tres condiciones se cumplen.

### 2.7 Resolución de documentos y reemplazo (entidad revisora, `/api/entidad-simulada/*` y `/api/tramites/*`)

Cierra el ciclo trámite → firma → revisión → resultado.

1. **Resolver** (`PATCH /api/entidad-simulada/documentos/{id}/resolucion`,
   gateado por `require_roles(admin, operador)`, mismo alcance por
   dependencia que ya aplicaba a verificar/descargar/borrar):
   `EntidadSimuladaFacade.resolver_documento` exige un motivo en texto plano
   solo si `decision == "RECHAZADO"`, y delega en
   `DocumentoTramitadoRepository.actualizar_resolucion`, cuyo `UPDATE` está
   condicionado a `WHERE estado_documento = 'EN TRAMITE'` — si no afecta
   ninguna fila (porque ya se resolvió, incluida una carrera entre dos
   operadores), la fachada lanza `DocumentoYaResueltoError` (409). Una
   resolución es definitiva: no existe endpoint de reversión para ningún
   rol.
2. **Consultar** (`GET /api/tramites/{dni}` y `.../buscar`, sin cambios de
   ruta): `TramiteResponse` ya trae `motivo_rechazo`/`fecha_resolucion`
   poblados cuando corresponde, sin exponer identidad del operador.
3. **Reemplazar** (`PATCH /api/tramites/{tramite_id}/reemplazo`, sin JWT —
   sigue el flujo público de ciudadano, igual que el resto de `tramites.py`):
   solo permitido si el trámite está `RECHAZADO` y la fecha actual no supera
   `fecha_respuesta` (el plazo, fijado desde el registro original, no desde
   la resolución). `DocumentoTramitadoRepository.actualizar_reemplazo`
   reabre el mismo trámite a `EN TRAMITE` (no crea uno nuevo) y limpia
   `motivo_rechazo`/`fecha_resolucion`.

`DocumentoTramitadoRepository` (antes definida dentro de
`rutas/entidad_simulada.py`) se reubicó a
`backend/src/repositorios/documento_tramitado_repo.py` para que
`entidad_simulada.py` y `tramites.py` compartan la misma escritura sobre
`documentos_tramitados` sin que un módulo de `rutas/` importe una clase
"repositorio" definida en otro módulo de `rutas/`. No tiene un adaptador en
memoria formal — los tests usan un fake duck-typed (`_FakeRepo` en
`test_entidad_simulada.py`), igual que antes de esta reubicación.

No se implementó ninguna notificación por correo al operador cuando se
firma un documento — decisión explícita: revisar la bandeja de pendientes
es responsabilidad activa del rol operador.

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

`backend/src/repositorios/documento_tramitado_repo.py`
(`DocumentoTramitadoRepository`) sigue el mismo rol para
`documentos_tramitados`, compartido por `rutas/entidad_simulada.py` y
`rutas/tramites.py` (ver 2.7) — pero, a diferencia de los anteriores, no
tiene un adaptador en memoria formal; sus tests usan un fake duck-typed
definido directamente en el archivo de test.

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

### 3.5 Patrones en firma-java (microservicios Java)

El subsistema de firma tiene su propio catálogo, independiente del backend
Python pero con el mismo criterio: un patrón por problema real.

#### Factory Method — `common-crypto/.../patterns/creational/{KeyPairFactory,RsaKeyPairFactory}.java`

Genera el par de llaves RSA sin acoplar a `identity-key-service` al
algoritmo concreto de generación; `SeedCitizenFactory`
(`identity-key-service`) la usa para sembrar llaves una sola vez por
ciudadano (`POST /api/personas/seed/once`, protegido con
`X-Internal-Token`, idempotente vía `key_seed_control`).

#### Adapter — `common-crypto/.../crypto/OriginalCryptoAdapter.java`

Traduce el protocolo de firma propio de la cátedra (RSA modular original,
no `java.security.Signature` estándar) a una interfaz simple
(`sha256Hex`, `signToBase64`) que `DocumentSignatureFacade` consume sin
conocer los detalles matemáticos.

#### Facade — `signature-service/.../service/DocumentSignatureFacade.java`

**Problema**: firmar un documento involucra 6 colaboradores (cliente de
identidad, preprocesador, criptografía, empaquetado, repositorio y
auditoría) — coordinarlos desde el controller mezclaría HTTP con lógica de
negocio.

**Solución**: `DocumentSignatureFacade` expone `sign`, `verify`,
`verifyUploaded`, `listByDni`, `deleteDocument` como la única superficie que
`DocumentController` conoce; internamente orquesta al resto de patrones de
esta sección.

#### Command — `signature-service/.../patterns/behavioral/SignDocumentCommand.java`

Encapsula los datos de una operación de firma (`dni`, `fileName`,
`contentType`, `content`) como un objeto inmutable que viaja desde el
controller hasta la fachada, desacoplando la forma HTTP (multipart) de la
lógica de firma.

#### Strategy — `signature-service/.../patterns/behavioral/{SignatureVerificationStrategy,RsaModularVerificationStrategy}.java`

Aísla el algoritmo de verificación de firma detrás de una interfaz, para
poder soportar otro esquema de firma en el futuro sin tocar
`DocumentSignatureFacade.verify()`.

#### Strategy (registro) — `signature-service/.../patterns/behavioral/{DocumentPreprocessor,DocumentPreprocessorRegistry,DefaultBinaryPreprocessor,PdfStampPreprocessor}.java`

**Problema**: preparar el documento antes de firmarlo difiere según el tipo
de archivo — un PDF necesita un sello visible, un binario genérico no.

**Solución**: `DocumentPreprocessorRegistry` elige en tiempo de ejecución
entre `PdfStampPreprocessor` y `DefaultBinaryPreprocessor` según el
`contentType`; agregar un formato nuevo (ej. DOCX) es una clase más, sin
tocar `DocumentSignatureFacade`.

### 3.6 Patrones evaluados y descartados (decisión consciente)

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
  (plugin Pydantic), `pytest --cov=src --cov-fail-under=85`. Cubre solo
  `backend/` — `frontend/` y `firma-java/` no tienen pipeline propio todavía.
- Estado tras la refactorización estructural: **151 tests, cobertura 92%**.
- Tests específicos de patrones:
  - `tests/test_mesa_de_partes_facade.py` (Facade + integración con Bridge)
  - `tests/test_solicitud_repo_auditoria.py` (Decorator)
  - `tests/test_ciudadano_cache_proxy.py` (Proxy: TTL, no-cacheo de fallos, desalojo)
  - `tests/test_notificaciones.py` (Bridge: mismo notificador × 3 canales)
  - `tests/test_cadena_aprobacion.py`, `tests/test_enrutamiento_service.py`,
    `tests/test_documento_factory.py` (patrones previos)
- **Huecos de cobertura conocidos**: `rutas/tramites.py` no tiene tests
  (backend); `firma-java/` (los tres módulos Maven) no tiene tests
  automatizados ni CI configurado.

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
