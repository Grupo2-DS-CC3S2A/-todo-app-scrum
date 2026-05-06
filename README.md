# Mesa de Partes — Sistema de Voto Electronico Seguro

[![Sprint](https://img.shields.io/badge/Scrum-Sprint%203-blue)](#)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI-brightgreen)](#)
[![Branching](https://img.shields.io/badge/flow-main%20%7C%20develop-orange)](#)

Implementacion de una Mesa de Partes para la automatizacion del voto electronico.
Reduce esperas y previene fraudes mediante cifrado hash y reglas evolutivas
derivadas de algoritmos geneticos.

> Proyecto del curso **Desarrollo de Software (CC3S2-A)** — Practicas Dirigidas 1 y 2.
> Arquitectura orientada a servicios + Scrum.

---

## Tabla de Contenidos

1. [Arquitectura](#arquitectura-del-sistema)
2. [Estructura del Repositorio](#estructura-del-repositorio)
3. [Requisitos](#requisitos-de-entorno)
4. [Inicializacion](#instrucciones-de-inicializacion)
5. [Flujo de Trabajo Git + Jira](#flujo-de-trabajo-git--jira)
6. [Integrantes](#integrantes-grupo-2)

---

## Arquitectura del Sistema

Construido bajo principios de **Clean Architecture** y **SOLID**.

| Capa | Tecnologia | Responsabilidad |
|------|------------|-----------------|
| Frontend | React + TypeScript + Vite + Chakra UI v3 | UI, custom hooks asincronos |
| Backend | Python + FastAPI | Endpoints seguros, transacciones asincronas |
| Seguridad | SHA-256 + Algoritmos Geneticos | Anonimizado y llaves dinamicas |

---

## Estructura del Repositorio

```
.
├── backend/                       # Servidor FastAPI, modelos Pydantic, cifrado
├── frontend/                      # Cliente React, hooks, tipado estricto
├── Informe_Estado_Proyecto.md     # Iteracion 1, Product Backlog, arquitectura
├── Reporte_Actividades_Miembros.md# Contribuciones del Grupo 2
└── README.md
```

---

## Requisitos de Entorno

- Node.js **>= 18**
- Python **>= 3.10**
- npm + pip

---

## Instrucciones de Inicializacion

Ejecutar en consolas separadas.

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Unix / macOS
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Portal web: `http://localhost:5173`

---

## Flujo de Trabajo Git + Jira

Ramas principales:

- **`main`** — protegida, solo recibe merges desde `develop` via Pull Request.
- **`develop`** — integracion continua del equipo.
- **`feature/SCRUM-XX-descripcion`** — derivada de `develop`, una por ticket Jira.

Ejemplo de ciclo completo:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/SCRUM-14-envio-solicitud

# ...trabajo...

git commit -m "SCRUM-14 #in-progress feat: envio de solicitud a dependencia"
git push -u origin feature/SCRUM-14-envio-solicitud

# Abrir Pull Request hacia develop en GitHub.
# Al hacer merge: Jira mueve el ticket a "Finalizado" automaticamente.
```

**Smart Commits** soportados:

| Marca | Efecto en Jira |
|-------|----------------|
| `SCRUM-14 #in-progress` | Mueve a *En curso* |
| `SCRUM-14 #review` | Mueve a *En revision* |
| `SCRUM-14 #done` o merge a `main` | Mueve a *Finalizado* |
| `SCRUM-14 #time 2h #comment "fix"` | Registra tiempo + comentario |

---

## Integrantes (Grupo 2)

- ALVARO JESUS TAIPE COTRINA
- Andrew Owim Inga Rojas
- CeSaR OmaR LoPeZ ArTeAgA
- Jose Alfredo Palomino
- LEONARDO CHACON
