# Dockerfile para SlideMotion - Configuración profesional
FROM python:3.12-slim

# Variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para PostgreSQL y procesamiento PDF
RUN apt-get update && apt-get install -y \
    # Librerías cliente de PostgreSQL
    libpq-dev \
    # Dependencias para procesamiento PDF
    poppler-utils \
    # Herramientas de compilación necesarias para algunas dependencias
    gcc \
    g++ \
    # Herramientas de red útiles para debugging
    netcat-openbsd \
    # Limpiar caché de apt
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Crear directorios de la aplicación
WORKDIR /app

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R appuser:appuser /app

# Actualizar pip a la última versión
RUN pip install --upgrade pip

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Cambiar permisos de todos los archivos al usuario appuser
RUN chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Exponer puerto 8000
EXPOSE 8000

# Health check para verificar que el servicio esté funcionando
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD nc -z localhost 8000 || exit 1

# Script de entrada por defecto (se puede sobrescribir en docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--reload", "slidemotion.wsgi:application"]