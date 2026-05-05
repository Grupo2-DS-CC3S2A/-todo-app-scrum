# Hoja de Ruta - Mesa de Partes de Voto Electrónico

## Estado Actual (Semana 7)
Se ha consolidado la versión **Beta** del sistema, implementada en gran medida por la integración core de arquitectura. Se tiene el backend en FastAPI (Clean Architecture), frontend en React (Chakra UI) y el motor de encriptación y hashes funcionando.

---

## Tareas Inmediatas para el Resto del Equipo (Para la presentación de mañana)
*Nota: Estas tareas están diseñadas para ser muy rápidas de implementar (1 hora o menos), de bajísima complejidad, pero que "visten" muy bien al proyecto y demuestran que todos trabajaron.*

1. **Andrew - Validación de Diseño Responsivo:**
   * **Acción:** Asegurar que el formulario web de votación se adapte perfectamente a celulares.
   * **Implementación:** Modificar o revisar las etiquetas del layout en React para garantizar que no se desborde la pantalla en tamaños pequeños.
2. **César - Pruebas de API con Postman:**
   * **Acción:** Crear una colección de pruebas documentadas para los endpoints del backend.
   * **Implementación:** Abrir Postman, crear un par de peticiones `POST` hacia el endpoint de votos de FastAPI, exportar el archivo `.json` y subirlo al repositorio.
3. **José - Accesibilidad (a11y) y Experiencia de Usuario (UX):**
   * **Acción:** Mejorar la accesibilidad visual de los componentes.
   * **Implementación:** Añadir atributos `aria-label` en los botones de React, revisar textos de alertas/toasts y corregir la ortografía de los menús.
4. **Leonardo - Redacción del Manual de Usuario Beta:**
   * **Acción:** Crear un pequeño manual "Paso a Paso" para los votantes.
   * **Implementación:** Redactar un PDF de 1 o 2 páginas con capturas de pantalla de cómo llenar el DNI y cómo leer el comprobante del hash encriptado.

---

## Plan de Producción (Semanas 8 a 15)

A partir de la semana 8, las tareas se distribuyen equitativamente para escalar el sistema Beta a Producción.

### Semana 8: Presentación Parcial y Feedback
* **Todos:** Exposición de la Beta actual. Recopilación de críticas del profesor y ajustes del backlog en Jira.

### Semanas 9 y 10: Autenticación y Base de Datos (Seguridad Real)
* **Alvaro:** Integración de JWT (Tokens) en el backend y control de sesiones seguras.
* **Andrew:** Creación de las pantallas de Login / Registro y vistas protegidas en el Frontend.
* **César:** Sustituir la memoria temporal de FastAPI por una Base de Datos real (PostgreSQL o SQLite) usando un ORM como SQLAlchemy.
* **José:** Pruebas QA de inyección SQL y control de vulnerabilidades del login.
* **Leonardo:** Encriptación de contraseñas de administradores y gestión de variables de entorno `.env`.

### Semanas 11 y 12: Panel de Administración y Estadísticas (Dashboard)
* **Alvaro:** Desarrollar los endpoints estadísticos en FastAPI que contabilizan votos de manera agregada sin comprometer el anonimato del DNI.
* **Andrew:** Implementar gráficos interactivos de resultados (diagramas de barras/pasteles) en React usando `Recharts`.
* **César:** Programar un exportador de Reportes PDF/Excel para las Actas de Escrutinio en el backend.
* **José:** Diseño del Mockup/Figma del Panel de Control de la ONPE/Administrador.
* **Leonardo:** Pruebas de auditoría: garantizar que la suma de votos coincida exactamente con los hashes generados.

### Semanas 13 y 14: Despliegue en la Nube (DevOps & Cloud)
* **Alvaro:** Crear los `Dockerfile` para empaquetar el frontend y el backend de forma automatizada.
* **Andrew:** Desplegar la aplicación web (React) en servicios gratuitos en la nube (Vercel o Netlify).
* **César:** Desplegar la API (FastAPI) en un servicio como Render, Railway o AWS.
* **José:** Configurar GitHub Actions (Integración Continua) para que los tests corran solos en cada *push*.
* **Leonardo:** Configurar CORS para producción y vincular dominios SSL (HTTPS).

### Semana 15: Pruebas de Estrés y Documentación de Cierre
* **Alvaro:** Refactorización final del código, verificando el cumplimiento estricto de SOLID.
* **Andrew:** Limpieza de código no usado, pulido de animaciones visuales.
* **César:** Optimización de velocidad de respuestas del backend.
* **José & Leonardo:** Ejecutar pruebas de carga masiva (ej. JMeter / Locust) simulando 1000 usuarios votando a la vez, y redactar el informe final del SRS.
