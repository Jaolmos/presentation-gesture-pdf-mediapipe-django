#!/bin/bash

# ============================================
# Script de despliegue para SlideMotion
# Uso en servidor de producción (DigitalOcean VPS)
# ============================================

set -e  # Detener el script si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# Verificar que estamos en el directorio correcto
# ============================================
if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "No se encontró docker-compose.prod.yml. ¿Estás en el directorio correcto?"
    exit 1
fi

# ============================================
# Verificar que existe .env
# ============================================
if [ ! -f ".env" ]; then
    print_error "No se encontró archivo .env"
    print_info "Copia .env.production.example como .env y configúralo:"
    print_info "  cp .env.production.example .env"
    print_info "  nano .env"
    exit 1
fi

# ============================================
# Cargar variables de entorno
# ============================================
source .env

# ============================================
# Verificar variables críticas
# ============================================
if [ -z "$DOMAIN" ]; then
    print_error "La variable DOMAIN no está configurada en .env"
    exit 1
fi

if [ -z "$ACME_EMAIL" ]; then
    print_error "La variable ACME_EMAIL no está configurada en .env"
    exit 1
fi

print_info "Desplegando SlideMotion para el dominio: $DOMAIN"

# ============================================
# Crear directorios necesarios
# ============================================
print_info "Creando directorios necesarios..."
mkdir -p traefik/letsencrypt
mkdir -p traefik/logs
mkdir -p backups
mkdir -p logs

# Permisos para acme.json (requerido por Traefik)
touch traefik/letsencrypt/acme.json
chmod 600 traefik/letsencrypt/acme.json

# ============================================
# Pull de imágenes actualizadas
# ============================================
print_info "Descargando imágenes Docker actualizadas..."
docker compose -f docker-compose.prod.yml pull

# ============================================
# Construir imagen de la aplicación
# ============================================
print_info "Construyendo imagen de la aplicación..."
docker compose -f docker-compose.prod.yml build --no-cache web

# ============================================
# Detener servicios existentes (si existen)
# ============================================
print_info "Deteniendo servicios existentes..."
docker compose -f docker-compose.prod.yml down

# ============================================
# Iniciar servicios
# ============================================
print_info "Iniciando servicios en producción..."
docker compose -f docker-compose.prod.yml up -d

# ============================================
# Esperar a que la base de datos esté lista
# ============================================
print_info "Esperando a que la base de datos esté lista..."
sleep 10

# ============================================
# Ejecutar migraciones
# ============================================
print_info "Ejecutando migraciones de base de datos..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# ============================================
# Crear superusuario (solo en primera instalación)
# ============================================
if [ "$1" == "--first-install" ]; then
    print_info "Primera instalación detectada. Creando superusuario..."
    docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
fi

# ============================================
# Verificar estado de los servicios
# ============================================
print_info "Verificando estado de los servicios..."
docker compose -f docker-compose.prod.yml ps

# ============================================
# Mostrar logs recientes
# ============================================
print_info "Mostrando logs recientes..."
docker compose -f docker-compose.prod.yml logs --tail=50

# ============================================
# Información final
# ============================================
echo ""
print_info "========================================="
print_info "¡Despliegue completado exitosamente!"
print_info "========================================="
echo ""
print_info "Tu aplicación estará disponible en:"
print_info "  - Aplicación principal: https://$DOMAIN"
print_info "  - Dashboard Traefik: https://traefik.$DOMAIN"
print_info "  - Monitor Celery (Flower): https://flower.$DOMAIN"
echo ""
print_warning "IMPORTANTE: Los certificados SSL pueden tardar unos minutos en generarse"
print_warning "Si tienes problemas con SSL, verifica los logs de Traefik:"
print_info "  docker compose -f docker-compose.prod.yml logs traefik -f"
echo ""
print_info "Comandos útiles:"
print_info "  - Ver logs: docker compose -f docker-compose.prod.yml logs -f"
print_info "  - Reiniciar servicios: docker compose -f docker-compose.prod.yml restart"
print_info "  - Detener todo: docker compose -f docker-compose.prod.yml down"
print_info "  - Backup BD: docker compose -f docker-compose.prod.yml exec db pg_dump -U \$DB_USER \$DB_NAME > backup.sql"
echo ""
