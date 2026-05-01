# Mesa de Partes - Sistema de Voto Electronico Seguro

Este repositorio contiene la implementacion de una Mesa de Partes para la automatizacion del voto electronico. El objetivo principal es reducir las largas esperas y prevenir fraudes en el proceso de votacion mediante el uso de encriptacion hash y la simulacion de algoritmos geneticos.

El desarrollo de este sistema obedece a las indicaciones de la Practica Dirigida 1 y 2, empleando una arquitectura orientada a servicios y la metodologia Scrum para la gestion y entrega de valor.

## Arquitectura del Sistema

El sistema esta construido siguiendo los principios de Clean Architecture y SOLID:

- **Frontend:** Construido con React, TypeScript, Vite y Chakra UI v3. Su diseno esta centrado en proveer una interaccion agil y robusta. Todo el manejo asincrono esta delegado a Custom Hooks.
- **Backend:** Desarrollado en Python con el framework FastAPI. Procesa las transacciones de manera asincrona y expone un endpoint seguro para la emision de votos.
- **Modulo de Seguridad Criptografica:** Antes de registrar cualquier voto, los datos sensibles son anonimizados mediante un cifrado SHA-256. La llave de cifrado se genera dinamicamente empleando reglas evolutivas derivadas de algoritmos geneticos para mitigar ataques de fuerza bruta.

## Estructura del Repositorio

- `/backend`: Logica del servidor, modelos Pydantic, excepciones centralizadas y utilidades de cifrado.
- `/frontend`: Codigo del cliente estructurado en componentes de interfaz, hooks para el manejo de estados de red y archivos de tipado estricto.
- `/Informe_Estado_Proyecto.md`: Resumen de la primera iteracion Scrum, el Product Backlog inicial y la definicion de la arquitectura base.
- `/Reporte_Actividades_Miembros.md`: Desglose general de las contribuciones de cada miembro del Grupo 2.

## Requisitos de Entorno

Para probar la solucion en un entorno local, verifique tener instalado:
- Node.js (version 18 o posterior)
- Python (version 3.10 o posterior)
- Administradores de paquetes (npm y pip)

## Instrucciones de Inicializacion

A continuacion se describen los comandos para ejecutar ambos entornos. Deben correrse en consolas separadas.

### Entorno Backend

```bash
cd backend
python -m venv .venv

# En Windows:
.venv\Scripts\activate
# En Unix/MacOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```
La documentacion automatica de la API (Swagger UI) estara expuesta en: `http://localhost:8000/docs`.

### Entorno Frontend

```bash
cd frontend
npm install
npm run dev
```
El portal web de la mesa de partes estara expuesto en: `http://localhost:5173`.

## Integracion y Flujo de Trabajo

La rama principal (`main`) se encuentra protegida. Toda contribucion al codigo fuente requiere la creacion de una rama derivada vinculada directamente a la clave de un ticket en Jira (por ejemplo, `feature/DEV-04`). Se exige el uso del estandar de confirmacion "Smart Commits" para asegurar la trazabilidad del codigo frente al Backlog del Sprint.

## Integrantes (Grupo 2)

* ALVARO JESUS TAIPE COTRINA
* Andrew Owim Inga Rojas
* CeSaR OmaR LoPeZ ArTeAgA
* Jose Alfredo Palomino
* LEONARDO CHACON
