# Informe de Estado del Proyecto — Mesa de Partes Virtual

## 1. Datos generales

- **Proyecto:** Mesa de Partes Virtual — registro, derivación, firma digital y resolución de trámites documentarios.
- **Curso:** Desarrollo de Software (CC3S2-A) — Grupo 2.
- **Repositorio:** [github.com/Grupo2-DS-CC3S2A/todo-app-scrum](https://github.com/Grupo2-DS-CC3S2A/todo-app-scrum)

## 2. Arquitectura actual

Tres servicios independientes: `backend/` (FastAPI, capas `rutas → servicios
→ repositorios → modelos`), `frontend/` (React + Vite SPA), `firma-java/`
(microservicios Java 21/Spring Boot para firma digital RSA). Persistencia en
Supabase/Postgres. Catálogo completo de patrones de diseño y flujos en
`docs/arquitectura-y-patrones.md`.

## 3. Funcionalidades entregadas

- Validación de identidad ciudadana por DNI.
- Registro de trámites con firma digital RSA (sello visible en PDF, contenedor `.uni-signed` verificable, envío por correo).
- Autenticación JWT con roles `admin`/`operador`, este último acotado a su dependencia asignada.
- Entidad revisora: listar, verificar firma, aceptar o rechazar documentos (motivo obligatorio al rechazar), con guard atómico contra resoluciones simultáneas.
- Consulta de estado y motivo por el ciudadano; reemplazo de documento rechazado mientras el plazo no haya vencido.

## 4. Calidad

- 194 tests automatizados (backend), 88% de cobertura (umbral CI 85%).
- `black`, `flake8`, `mypy` sin errores.
- CI en cada push/PR a cualquier rama (`ci.yml`).

## 5. Despliegue

- **Backend:** Google Cloud Run (`us-central1`), imagen Docker multi-stage.
- **Frontend:** Vercel.
- **Base de datos:** Supabase Cloud; migraciones aplicadas automáticamente en cada push (`docker-ci.yml`).
- **Firma digital:** `identity-key-service` y `signature-service` en Cloud Run (`europe-west1`), desplegados en workflow aparte al tocar `firma-java/`.

## 6. Equipo

| Nombre                     |
| -------------------------- |
| Alvaro Jesus Taipe Cotrina |
| César Omar López Arteaga   |
| Jose Alfredo Palomino      |
| Leonardo Chacón Roque      |
