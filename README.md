# Mesa de Partes — Voto Electrónico Seguro

[![CI](https://github.com/Grupo2-DS-CC3S2A/-todo-app-scrum/actions/workflows/ci.yml/badge.svg)](https://github.com/Grupo2-DS-CC3S2A/-todo-app-scrum/actions/workflows/ci.yml)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI-brightgreen)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green)](#)

Sistema de **Mesa de Partes Electrónica** para la automatización del registro y derivación de solicitudes de voto. Reduce tiempos de espera y previene fraudes mediante cifrado SHA-256 y llaves dinámicas generadas por algoritmos genéticos.

> Proyecto del curso **Desarrollo de Software (CC3S2-A)** — Grupo 2.

---

## ¿Qué hace el sistema?

El sistema cubre dos grandes flujos:

| Funcionalidad                 | Descripción                                                                                                                                                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Emisión de voto seguro**    | El ciudadano ingresa su DNI e ID de candidato. El backend genera un hash SHA-256 del voto junto con una llave evolutiva producida por un algoritmo genético. Se devuelve un comprobante con hash, llave y timestamp. |
| **Derivación de solicitudes** | Un administrador puede derivar solicitudes a la dependencia correspondiente (Registro Civil, Identificación, GRIAS, Imagenología, etc.) según el tipo de trámite.                                                    |
| **Auditoría**                 | Endpoint de auditoría que devuelve todos los votos cifrados almacenados para verificación interna.                                                                                                                   |
| **Consulta de estado**        | Permite consultar el estado de una solicitud derivada por su ID.                                                                                                                                                     |
| **Health check**              | Endpoint `/health` para monitoreo de disponibilidad del servicio.                                                                                                                                                    |

> **Nota sobre persistencia:** Actualmente el repositorio de solicitudes es **en memoria** (se reinicia al apagar el servidor). No hay base de datos relacional conectada aún — es el siguiente paso planificado en el roadmap.

---

## Organización del Repositorio

```
VotingSystem/
├── backend/                    # API REST con FastAPI (Python)
│   ├── app.py                  # Punto de entrada (uvicorn)
│   ├── requirements.txt        # Dependencias Python
│   └── src/
│       ├── config.py           # Configuración centralizada (env vars)
│       ├── main.py             # App factory de FastAPI + CORS + routers
│       ├── modelos/            # Entidades de dominio (Pydantic)
│       ├── servicios/          # Lógica de negocio (cifrado, GA, derivación)
│       ├── repositorios/       # Capa de persistencia (en memoria / reemplazable)
│       ├── rutas/              # Endpoints: votos, admin, solicitudes
│       ├── excepciones/        # Errores de dominio y handlers HTTP
│       ├── utilidades/         # SHA-256, algoritmo genético de llaves
│       └── logging_config.py   # Logging estructurado
│
├── frontend/                   # SPA con React + TypeScript + Vite
│   ├── index.html
│   └── src/
│       ├── App.tsx             # Layout principal (split panel institucional)
│       ├── components/
│       │   ├── VotingForm.tsx       # Formulario de voto (DNI + candidato)
│       │   ├── VotingReceipt.tsx    # Comprobante del voto cifrado
│       │   └── AdminDerivacionPanel.tsx  # Panel de administración
│       ├── hooks/
│       │   └── useVoting.ts    # Hook asíncrono: fetch + estado de carga
│       ├── api/                # Funciones de llamada al backend
│       └── types/              # Tipos TypeScript compartidos
│
└── README.md
```

---

## Tecnologías

### Backend

| Tecnología               | Uso                                                        |
| ------------------------ | ---------------------------------------------------------- |
| **Python 3.10+**         | Lenguaje principal del servidor                            |
| **FastAPI**              | Framework web asíncrono, genera Swagger UI automáticamente |
| **Uvicorn**              | Servidor ASGI de alta performance                          |
| **Pydantic v2**          | Validación y serialización de datos                        |
| **SHA-256** (stdlib)     | Cifrado del voto para garantizar anonimato                 |
| **Algoritmos Genéticos** | Generación de llaves evolutivas dinámicas                  |

### Frontend

| Tecnología                | Uso                                                    |
| ------------------------- | ------------------------------------------------------ |
| **React 18 + TypeScript** | UI reactiva con tipado estricto                        |
| **Vite**                  | Bundler y servidor de desarrollo ultrarrápido          |
| **Chakra UI v3**          | Sistema de componentes con paleta institucional RENIEC |

### Infraestructura / Flujo

| Herramienta              | Uso                                                          |
| ------------------------ | ------------------------------------------------------------ |
| **Git + GitHub**         | Control de versiones, ramas `main` / `develop` / `feature/*` |
| **Jira (Smart Commits)** | Trazabilidad de tickets desde los mensajes de commit         |

---

## Cómo ejecutar el proyecto

Abrir **dos terminales** en la raíz de `VotingSystem/`.

### 1. Backend

```bash
cd backend

# Crear y activar entorno virtual (solo la primera vez)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

- API en: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install        # solo la primera vez
npm run dev
```

- Portal web: `http://localhost:5173`

---

## Integrantes — Grupo 2

| Nombre                     |
| -------------------------- |
| Alvaro Jesus Taipe Cotrina |
| Andrew Owim Inga Rojas     |
| César Omar López Arteaga   |
| Jose Alfredo Palomino      |
| Leonardo Chacón            |
