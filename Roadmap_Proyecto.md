# Hoja de Ruta — Mesa de Partes de Voto Electrónico

## Estado del Proyecto

La versión **Beta** se encuentra en producción de referencia con arquitectura Clean en FastAPI, frontend React + Chakra UI, motor de cifrado SHA-256 y algoritmo genético de llaves operativo. El Sprint 1 cerró al **100%** tras completar la suite de pruebas unitarias (DEV-07).

---

## Sprint 1 — Arquitectura Base y Cifrado `[DONE]`

| Feature | HU | SP | Estado |
|---|---|---|---|
| Arquitectura Clean Architecture (backend + frontend) | HU-01 | 8 | Done |
| Endpoint POST /api/votar con cifrado SHA-256 | HU-02 | 5 | Done |
| Módulo de Algoritmo Genético de llaves | HU-03 | 5 | Done |
| Formulario de votación y comprobante (frontend) | HU-02 | 5 | Done |
| Endpoint GET /api/votos_audit | HU-02 | 3 | Done |
| Sistema de derivación de solicitudes básico | HU-04 | 5 | Done |
| Health check endpoint `/health` | HU-01 | 1 | Done |
| Suite de pruebas unitarias — 97% cobertura | DEV-07 | 3 | Done |
| Integración Jira ↔ GitHub (Smart Commits) | DEV-08 | 1 | Done |
| Documentación README y roadmap inicial | DEV-09 | 1 | Done |

**Velocidad del sprint:** 37 SP entregados

---

## Sprint 2 — Persistencia, Autenticación y Testing `[IN PROGRESS]`

**Objetivo del sprint:** Migrar de almacenamiento en memoria a base de datos relacional, implementar autenticación JWT y consolidar la cobertura de pruebas de integración.

| Feature / Epic | Ticket | SP | Prioridad |
|---|---|---|---|
| Migración a PostgreSQL con SQLAlchemy + Alembic | S2-01 | 13 | Crítica |
| Autenticación JWT y control de sesión | S2-05 | 8 | Crítica |
| Validación contra padrón electoral (mock) | S2-02 | 8 | Alta |
| Tests de integración con BD y autenticación | S2-03 | 8 | Alta |
| CI/CD con GitHub Actions | S2-04 | 5 | Alta |
| Panel de administración RENIEC (frontend + backend) | S2-06 | 8 | Media |
| GitHub for Jira — automatización de transiciones | S2-08 | 2 | Media |
| Documentación API Swagger + README actualizado | S2-09 | 3 | Media |

**Story Points estimados:** 55 SP

### Detalle de features críticas

**S2-01 — Migración a PostgreSQL**
- Modelos ORM: `Voto`, `Solicitud`, `Usuario`
- Migraciones con Alembic
- Repositorios SQL que reemplazan los adaptadores en memoria
- Variable de entorno `DATABASE_URL`

**S2-05 — Autenticación JWT**
- Endpoint `POST /api/auth/login` → retorna JWT con claims `sub`, `rol`, `exp`
- Middleware de validación de token en `Authorization` header
- Protección de `/api/votos_audit` y `/api/admin/*` con rol `admin`
- Contraseñas hasheadas con bcrypt (factor 12), tokens con expiración 24 h

**S2-02 — Validación contra padrón electoral**
- Endpoint mock `GET /api/padron/{dni}` que simula consulta a RENIEC
- Validación en `VotoService`: DNI en padrón, habilitado, no ha votado
- Nuevas excepciones de dominio: `CiudadanoNoHabilitadoError`, `YaVotoError`

**S2-04 — CI/CD GitHub Actions**
- Pipeline: lint (flake8 + mypy + black) → pytest con cobertura → fallo si < 85%
- Protección de rama `main`: merge bloqueado si CI falla

### Definition of Done — Sprint 2
- Votos persisten tras reiniciar el servidor
- Endpoints sensibles rechazados sin token válido (401 / 403)
- Cobertura de tests ≥ 90% (integración + unitarios)
- CI ejecutándose en cada PR con badge verde en README
- Swagger actualizado con esquemas de autenticación

---

## Sprint 3 — Dashboard y Estadísticas `[BACKLOG]`

**Objetivo:** Panel de administración avanzado con visualización de datos, reportes y auditoría de integridad.

| Feature | Ticket | SP |
|---|---|---|
| Endpoints estadísticos agregados (votos/hora, votos/dependencia) | S3-01 | 8 |
| Gráficos interactivos con Recharts | S3-02 | 8 |
| Exportador de reportes PDF / CSV | S3-03 | 8 |
| Diseño UI/UX del panel admin (Figma + style guide) | S3-04 | 5 |
| Endpoint de verificación de integridad de BD | S3-05 | 5 |
| Logging estructurado (JSON) y monitoreo | S3-06 | 8 |

**Story Points estimados:** 42 SP

---

## Sprint 4 — DevOps y Despliegue en Producción `[BACKLOG]`

**Objetivo:** Contenedorización completa y despliegue en nube con alta disponibilidad.

| Feature | Ticket | SP |
|---|---|---|
| Dockerización multi-stage (backend + frontend + PostgreSQL) | S4-01 | 8 |
| Despliegue frontend en Vercel / Netlify | S4-02 | 5 |
| Despliegue backend en Render / Railway / AWS | S4-03 | 8 |
| Configuración CORS y headers de seguridad para producción | S4-04 | 3 |
| Monitoreo de producción (UptimeRobot + alertas) | S4-05 | 5 |
| SSL y dominio personalizado | S4-06 | 5 |

**Story Points estimados:** 34 SP

---

## Sprint 5 — Optimización y Pruebas de Carga `[BACKLOG]`

**Objetivo:** Garantizar rendimiento bajo carga masiva y documentación de cierre del proyecto.

| Feature | Ticket | SP |
|---|---|---|
| Refactorización SOLID y code review final | S5-01 | 8 |
| Limpieza de código frontend (lazy loading, bundle split) | S5-02 | 5 |
| Optimización de queries SQL (índices, paginación) | S5-03 | 5 |
| Pruebas de carga con Locust — 1 000 usuarios concurrentes | S5-04 | 8 |
| Pruebas de seguridad (OWASP ZAP, inyección, XSS, CSRF) | S5-05 | 5 |
| Documentación final (manual usuario, admin y técnico) | S5-06 | 3 |

**Story Points estimados:** 34 SP

---

## Resumen del Backlog

| Sprint | Epic principal | SP | Estado |
|---|---|---|---|
| Sprint 1 | Arquitectura base + cifrado | 37 | Done |
| Sprint 2 | Persistencia + autenticación | 55 | In Progress |
| Sprint 3 | Dashboard + estadísticas | 42 | Backlog |
| Sprint 4 | DevOps + producción | 34 | Backlog |
| Sprint 5 | Optimización + cierre | 34 | Backlog |
| **Total** | | **202 SP** | **18% completado** |
