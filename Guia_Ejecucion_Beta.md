# Guía de Compilación y Ejecución (Versión Beta)

Este documento es una guía rápida para levantar el proyecto localmente y detalla los puntos clave que deben mostrarse durante la presentación o revisión de la versión Beta.

## 1. Instrucciones de Compilación y Ejecución

Debes levantar ambos sistemas (Backend y Frontend) en terminales separadas.

### Levantamiento del Servidor (Backend - Python)
El backend procesa la encriptación mediante hashes y simulación de algoritmos genéticos.

1. Abre una terminal y dirígete a la carpeta del backend:
   ```bash
   cd VotingSystem/backend
   ```
2. Activa el entorno virtual (si ya ejecutaste esto una vez, no es necesario instalar las dependencias de nuevo):
   ```bash
   # En Windows:
   .venv\Scripts\activate
   # Si faltan dependencias corre: pip install -r requirements.txt
   ```
3. Ejecuta el servidor en modo desarrollo:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```
   *El servidor quedará corriendo en `http://localhost:8000`.*

### Levantamiento del Cliente Web (Frontend - React)
El frontend proporciona la interfaz gráfica web usando React y Chakra UI.

1. Abre una **nueva** terminal (manteniendo abierta la del backend) y dirígete al frontend:
   ```bash
   cd VotingSystem/frontend
   ```
2. Inicia el servidor de desarrollo web:
   ```bash
   npm run dev
   ```
   *La aplicación estará disponible en `http://localhost:5173`.*

---

## 2. ¿Qué debes mostrar durante la presentación? (Guía de Exposición)

Durante la demostración del sistema Beta, sigue este flujo para impresionar al profesor:

### A. La Interfaz y Arquitectura (Frontend)
*   **Abre `localhost:5173` en el navegador.**
*   Muestra el diseño. Explica que no es simple HTML, sino una **Arquitectura Limpia en React**, fuertemente tipada con TypeScript y usando **Chakra UI** para los componentes.

### B. Pruebas de Validación Inmediata
*   **El Error Intencional:** Intenta hacer clic en "Votar" dejando los datos vacíos o poniendo un DNI de 3 letras.
*   **Lo que ocurre:** Saltará una notificación roja elegante (Toast) indicando el error. Explica que esto evita sobrecargar el servidor con datos basura y demuestra una alta atención a la **Experiencia de Usuario (UX)**.

### C. El Core del Sistema (Votación y Encriptación)
*   **Flujo Correcto:** Ingresa un DNI de 8 números válido y selecciona un candidato. Dale a Votar.
*   **Lo que ocurre:** El botón mostrará un ícono de carga. Inmediatamente después, aparecerá en pantalla un "Comprobante de Voto".
*   **El Punto Clave de Venta:** Muestra el `Código Hash` que aparece en el comprobante. Explícale a la audiencia que **el DNI original no se guarda en crudo**. El backend recibe el voto, aplica algoritmos de criptografía (simulados con algoritmos genéticos) y devuelve ese Hash. Esto garantiza que nadie (ni el administrador) pueda saber por quién votó esa persona, eliminando cualquier fraude.

### D. Verificación de Consola (Backend)
*   **La Prueba Técnica:** Abre la terminal negra donde está corriendo Python (FastAPI).
*   **Lo que ocurre:** Verás que la consola imprimió mensajes como "Voto registrado exitosamente...". Explica que FastAPI está procesando las solicitudes de forma completamente asíncrona, haciéndolo capaz de soportar múltiples votos simultáneos sin colapsar.
