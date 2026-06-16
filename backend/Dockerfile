# Multi-etapa

# Etapa 1: Constructor
FROM python:3.10-slim AS builder

# Evitar que Python genere archivos .pyc y forzar que la salida no use buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Crear y activar un entorno virtual para aislar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Instalar dependencias puras de producción
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Etapa 2: Producción
FROM python:3.10-slim

# Mantener variables de entorno optimizadas
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configurar la ruta para usar el entorno virtual de la etapa anterior
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Crear un usuario sin privilegios root por seguridad
RUN addgroup --system appgroup && adduser --system --group appuser

# Copiar el entorno virtual limpio desde la etapa 1
COPY --from=builder /opt/venv /opt/venv

# Copiar solo la carpeta src con el código de la aplicación
COPY src/ ./src/

# Otorgar los permisos de la carpeta al usuario seguro
RUN chown -R appuser:appgroup /app

# Cambiar del usuario root al nuevo usuario seguro
USER appuser

# Exponer el puerto por defecto de FastAPI
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]