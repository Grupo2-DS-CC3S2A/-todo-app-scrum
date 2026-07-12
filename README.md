# Mesa de Partes Virtual

[![CI](https://github.com/Grupo2-DS-CC3S2A/todo-app-scrum/actions/workflows/ci.yml/badge.svg)](https://github.com/Grupo2-DS-CC3S2A/todo-app-scrum/actions/workflows/ci.yml)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20Java-brightgreen)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)](#)

Sistema de **Mesa de Partes Virtual**: registro, derivación, firma digital y
resolución de trámites documentarios. Reemplaza la ventanilla física por un
flujo digital trazable, con firma RSA verificable y una entidad revisora que
acepta o rechaza cada documento.

> Proyecto del curso **Desarrollo de Software (CC3S2-A)** -> Grupo 2.

---

## Índice

- [Arquitectura](#arquitectura)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Funcionalidades principales](#funcionalidades-principales)
- [Patrones de diseño](#patrones-de-diseño)
- [Cómo ejecutar](#cómo-ejecutar)
- [Testing](#testing)
- [Calidad](#calidad)
- [Despliegue](#despliegue)
- [Integrantes -> Grupo 2](#integrantes--grupo-2)

---

## Arquitectura

Tres servicios independientes:

| Servicio | Stack | Rol |
| --- | --- | --- |
| `backend/` | FastAPI, Python 3.10+ | API REST: validación ciudadana, trámites, auth JWT, resolución/reemplazo de documentos |
| `frontend/` | React 18 + TypeScript + Vite | SPA: portal del ciudadano + panel "Entidad Simulada" para operador/admin |
| `firma-java/` | Java 21 + Spring Boot | Microservicios de firma digital RSA (`identity-key-service`, `signature-service`) |

Persistencia en **Supabase/Postgres**. Dependencia de capas en el backend:
`rutas → servicios → repositorios → modelos` (una capa nunca depende de la
que está por encima). El frontend es una SPA sin librería de ruteo, con
estado vía React hooks/Context, que habla directo con dos backends: la API
FastAPI y el `signature-service` de Java para el flujo de firma.

---

## Estructura del repositorio

```
todo-app-scrum/
├── backend/          # API REST FastAPI (rutas → servicios → repositorios → modelos)
├── frontend/         # SPA React + TypeScript + Vite
├── firma-java/       # Módulos Maven: common-crypto, identity-key-service, signature-service
└── supabase/         # Config local y migraciones (supabase/migrations/)
```

---

## Funcionalidades principales

- **Validación ciudadana** por DNI (`POST /api/validate`).
- **Registro y firma digital** de documentos, con sello visible en el PDF y contenedor `.uni-signed` verificable.
- **Entidad revisora** (roles admin/operador, JWT, acotado por dependencia): lista, verifica firma, acepta o rechaza cada documento con motivo obligatorio, y puede cerrar sesión de forma explícita.
- **Consulta y reemplazo**: el ciudadano ve el resultado y el motivo de rechazo; si el plazo no venció, puede registrar un documento de reemplazo.

---

## Patrones de diseño

El backend usa GoF de forma puntual, uno por problema real, no como adorno:

| Patrón | Dónde |
| --- | --- |
| Facade | `servicios/mesa_de_partes_facade.py` -> unifica derivación, sugerencia y notificación |
| Chain of Responsibility | `servicios/cadena_aprobacion.py` -> validación ciudadano → aprobación legal → derivación |
| Strategy | `servicios/enrutamiento_service.py` -> motor genético vs. reglas deterministas |
| Bridge | `servicios/notificaciones.py` -> qué se notifica × por qué canal |
| Decorator | `repositorios/solicitud_repo_auditoria.py` -> auditoría alrededor de cualquier `SolicitudRepository` |
| Proxy | `repositorios/ciudadano_repo.py` -> caché TTL sobre el repositorio real |
| Repository/Adapter | cada repositorio tiene adaptador en memoria (tests) y Supabase (prod) |
| Factory Method | `modelos/documento_solicitante.py` -> valida documentos DNI vs. RUC |

---

## Cómo ejecutar

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn src.main:app --reload --port 8000   # http://localhost:8000/docs

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# Firma digital (opcional, por módulo)
cd firma-java/signature-service && mvn spring-boot:run   # :8083
```

Requiere una instancia de Supabase (local vía `supabase start`, o Cloud) con
las migraciones de `supabase/migrations/` aplicadas.

---

## Testing

```bash
# Backend -> suite completa con cobertura (falla si < 85%)
cd backend && pytest --cov=src --cov-fail-under=85

# Backend -> un solo test
pytest tests/test_endpoints.py::TestEndpointHealth::test_health_retorna_200
pytest -k "test_health_retorna_200"

# Backend -> estilo y tipos
black --check src/ && flake8 src/ && mypy src/

# firma-java -> por módulo
cd firma-java/signature-service && mvn test
```

El frontend aún no tiene test runner ni lint script configurados.

---

## Calidad

- **194 tests** automatizados, **88% cobertura** (umbral CI: 85%).
- `black` · `flake8` · `mypy` limpios.
- CI en cada push/PR (`.github/workflows/ci.yml`); despliegue automático a Cloud Run + migración de Supabase en cada push (`docker-ci.yml`).
- `firma-java/` y `frontend/` aún no tienen pipeline de CI propio.

---

## Despliegue

Backend → Google Cloud Run · Frontend → Vercel · Base de datos → Supabase
Cloud · Microservicios de firma → Cloud Run (región `europe-west1`).

---

## Integrantes -> Grupo 2

| Nombre                     |
| -------------------------- |
| Alvaro Jesus Taipe Cotrina |
| César Omar López Arteaga   |
| Jose Alfredo Palomino      |
| Leonardo Chacón Roque      |
