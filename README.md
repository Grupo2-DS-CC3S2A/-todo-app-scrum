# Mesa de Partes Virtual

[![CI](https://github.com/Grupo2-DS-CC3S2A/todo-app-scrum/actions/workflows/ci.yml/badge.svg)](https://github.com/Grupo2-DS-CC3S2A/todo-app-scrum/actions/workflows/ci.yml)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20Java-brightgreen)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)](#)

Sistema de **Mesa de Partes Virtual**: registro, derivación, firma digital y
resolución de trámites documentarios. Reemplaza la ventanilla física por un
flujo digital trazable, con firma RSA verificable y una entidad revisora que
acepta o rechaza cada documento.

> Proyecto del curso **Desarrollo de Software (CC3S2-A)** — Grupo 2.

---

## Arquitectura

Tres servicios independientes:

| Servicio | Stack | Rol |
| --- | --- | --- |
| `backend/` | FastAPI, Python 3.10+ | API REST: validación ciudadana, trámites, auth JWT, resolución/reemplazo de documentos |
| `frontend/` | React 18 + TypeScript + Vite | SPA: portal del ciudadano + panel "Entidad Simulada" para operador/admin |
| `firma-java/` | Java 21 + Spring Boot | Microservicios de firma digital RSA (`identity-key-service`, `signature-service`) |

Persistencia en **Supabase/Postgres**. Detalle de capas, flujos y catálogo de
patrones de diseño en [`docs/arquitectura-y-patrones.md`](docs/arquitectura-y-patrones.md).

---

## Funcionalidades principales

- **Validación ciudadana** por DNI (`POST /api/validate`).
- **Registro y firma digital** de documentos, con sello visible en el PDF y contenedor `.uni-signed` verificable.
- **Entidad revisora** (roles admin/operador, JWT, acotado por dependencia): lista, verifica firma, acepta o rechaza cada documento con motivo obligatorio.
- **Consulta y reemplazo**: el ciudadano ve el resultado y el motivo de rechazo; si el plazo no venció, puede registrar un documento de reemplazo.

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

## Calidad

- **194 tests** automatizados, **88% cobertura** (umbral CI: 85%).
- `black` · `flake8` · `mypy` limpios.
- CI en cada push/PR (`.github/workflows/ci.yml`); despliegue automático a Cloud Run + migración de Supabase en cada push (`docker-ci.yml`).

---

## Despliegue

Backend → Google Cloud Run · Frontend → Vercel · Base de datos → Supabase
Cloud · Microservicios de firma → Cloud Run (región `europe-west1`).

---

## Integrantes — Grupo 2

| Nombre                     |
| -------------------------- |
| Alvaro Jesus Taipe Cotrina |
| César Omar López Arteaga   |
| Jose Alfredo Palomino      |
| Leonardo Chacón Roque      |
