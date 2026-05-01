# Informe de Estado de Proyecto - Iteración 1 (Scrum)

## 1. Datos Generales
- **Proyecto:** Mesa de Partes para Automatización de Voto Electrónico Seguro
- **Objetivo:** Automatizar el proceso de votación de forma electrónica, eliminando las demoras y largas esperas, y previniendo el fraude mediante cifrado hash y algoritmos genéticos.
- **Enlace a Jira:** [Tablero Scrum - Grupo 2](https://grupo-2-cc3s2.atlassian.net/jira/software/projects/SCRUM/boards)
- **Enlace a GitHub:** [Repositorio del Proyecto](https://github.com/Grupo2-DS-CC3S2A/-todo-app-scrum)

## 2. Arquitectura del Sistema (Práctica Dirigida 1)
Para cumplir con los requerimientos de seguridad, rendimiento y adaptabilidad, se define la siguiente arquitectura orientada a servicios (Microservicios/Monolito Modular):

- **Frontend (Cliente Web):** React con Vite y Chakra UI. Proporciona una interfaz ágil para que los usuarios emitan su voto sin demoras.
- **Backend (API Core):** Node.js (Fastify/Express) o Python (FastAPI). Encargado de la lógica de negocio, validación de identidad y recepción de votos. Python es altamente recomendado para integrar fácilmente las librerías de algoritmos genéticos.
- **Módulo de Seguridad (Cifrado y Algoritmos Genéticos):** Un servicio que recibe el voto, le aplica un cifrado Hash (ej. SHA-256) y utiliza un algoritmo genético para mutar/evolucionar claves de cifrado dinámicas que previenen ataques de fuerza bruta y garantizan la inmutabilidad del voto.
- **Base de Datos:** PostgreSQL para datos relacionales de usuarios y auditoría, o MongoDB para almacenar los votos cifrados como documentos.

## 3. Product Backlog Inicial
A continuación, el Product Backlog derivado del Documento de Especificación de Requisitos de Software (SRS):

| ID | Tipo | Historia de Usuario / Requisito | Prioridad | Estimación (Puntos) |
|---|---|---|---|---|
| PB-01 | Epic | **Gestión de Identidad** | Alta | 21 |
| PB-02 | Epic | **Emisión de Voto Electrónico** | Alta | 34 |
| PB-03 | Epic | **Cifrado y Seguridad Antifraude** | Crítica | 40 |
| PB-04 | Story | Como votante, quiero registrarme en el sistema para validar mi identidad antes de votar. | Alta | 5 |
| PB-05 | Story | Como votante, quiero acceder a la mesa de partes electrónica para emitir mi voto de forma rápida. | Alta | 8 |
| PB-06 | Story | Como sistema, quiero cifrar cada voto emitido utilizando un hash criptográfico para garantizar el anonimato. | Crítica| 13 |
| PB-07 | Story | Como sistema, quiero aplicar algoritmos genéticos en la generación de llaves de cifrado para mitigar intentos de fraude. | Crítica| 21 |

## 4. Sprint 1 Backlog
Para esta primera iteración, el objetivo del Sprint es: **"Definir el Documento de Especificación de Requisitos de Software (SRS), establecer la arquitectura base y crear los flujos iniciales de registro y encriptación."**

| Ticket Jira | Tarea | Estado actual (Kanban/Scrum) | Asignado a |
|---|---|---|---|
| DEV-01 | Redactar Documento SRS inicial con Casos de Uso y Reglas de Negocio. | Done | Analista de Negocio |
| DEV-02 | Definir e inicializar arquitectura del repositorio (Frontend/Backend). | In Progress | Desarrollador |
| DEV-03 | Configurar integración entre Jira y GitHub (Smart Commits). | Done | Desarrollador / DevOps |
| DEV-04 | Implementar endpoint básico para recibir voto y generar Hash. | To Do | Desarrollador |
| DEV-05 | Diseñar plan de pruebas para la integridad del Hash. | To Do | Tester |

## 5. Reporte de Herramientas Ágiles
- **Jira:** Se ha configurado un proyecto tipo Scrum. Los tickets DEV-01 a DEV-05 han sido ingresados al Sprint 1 activo.
- **GitHub:** Se crearon ramas (branches) siguiendo el estándar `feature/DEV-XX-nombre-tarea`. La integración permite que al hacer un Pull Request, las tareas en Jira se muevan automáticamente a "In Review".
