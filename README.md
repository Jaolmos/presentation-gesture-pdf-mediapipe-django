# SlideMotion 🎯

SlideMotion es una aplicación web Django que permite controlar presentaciones PDF mediante gestos usando la cámara web. La idea es simple, levantas el brazo derecho para avanzar al siguiente slide, y el brazo izquierdo para retroceder.

## Características

- **Control por gestos**: Navega entre slides usando gestos de mano detectados por MediaPipe
- **Conversión automática**: Sube un PDF y se convierte automáticamente en slides individuales
- **Procesamiento asíncrono**: Conversión de PDFs en segundo plano con Celery
- **Modo presentación**: Vista fullscreen optimizada con navegación fluida
- **Configuración de cámara**: Selector y preview de cámara en tiempo real
- **Privacidad-first**: Detección de gestos en el navegador, no se envía video al servidor

## Tecnologías

### Backend
- Django 5.2 + Python 3.12
- PostgreSQL 16
- Redis 7 (cache + broker Celery)
- Celery (procesamiento asíncrono)
- pdf2image + Pillow (conversión PDF)

### Frontend
- Django Templates
- htmx (interactividad)
- Tailwind CSS v3.4
- MediaPipe JavaScript (detección gestos)

### Infraestructura
- Docker + Docker Compose
- Traefik v3.2 (proxy inverso + SSL automático)
- Gunicorn (servidor WSGI producción)
- WhiteNoise (servir archivos estáticos en producción)
- Flower (monitoreo Celery)

## Capturas de pantalla

![Screenshot principal](docs/screenshots/home.png)
![Modo presentación](docs/screenshots/presentation-mode.png)

## Instalación y uso (Desarrollo)

### Prerrequisitos

- Docker y Docker Compose instalados
- Git

### Clonar el repositorio

```bash
git clone https://github.com/Jaolmos/pdf-django-presentation-gesture-mediapipe.git
cd pdf-django-presentation-gesture-mediapipe
```

### Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.develop.example .env

# Editar si es necesario (valores por defecto funcionan para desarrollo)
nano .env
```

### Iniciar con Docker Compose

```bash
# Construir e iniciar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

### Ejecutar migraciones y crear superusuario

```bash
# Aplicar migraciones de base de datos
docker-compose exec web python manage.py migrate

# Crear superusuario para acceder al panel de administración
docker-compose exec web python manage.py createsuperuser
```

Sigue las instrucciones para crear tu cuenta de administrador (nombre de usuario, email y contraseña).

### Acceder a la aplicación

- **Aplicación principal**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin/ (usa las credenciales del superusuario)
- **Flower (monitor Celery)**: http://localhost:5555

### Panel de Administración Django

El panel de administración de Django te permite:
- Gestionar usuarios y permisos
- Ver y editar presentaciones directamente
- Administrar slides de cada presentación
- Monitorear el contenido de la base de datos
- Realizar operaciones de mantenimiento

Accede con las credenciales del superusuario que creaste anteriormente.

### Comandos útiles

```bash
# Ver logs de un servicio específico
docker-compose logs web -f
docker-compose logs celery -f

# Reiniciar un servicio
docker-compose restart web

# Ejecutar comandos Django
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py collectstatic

# Ejecutar tests
docker-compose exec web python -m pytest

# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes (borra datos)
docker-compose down -v
```

## Servicios Docker

La aplicación utiliza los siguientes servicios en desarrollo:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `web` | 8000 | Aplicación Django |
| `db` | 5432 | PostgreSQL |
| `redis` | 6379 | Cache y broker Celery |
| `celery` | - | Worker para procesamiento asíncrono |
| `flower` | 5555 | Monitor de tareas Celery |
| `tailwind` | - | Watcher de Tailwind CSS |

## Desarrollo Frontend

```bash
# El watcher de Tailwind se ejecuta automáticamente con docker-compose up

# Si necesitas compilar CSS manualmente:
docker-compose exec web python manage.py tailwind build
```

## Tests

```bash
# Ejecutar todos los tests
docker-compose exec web python -m pytest

# Ejecutar tests con cobertura
docker-compose exec web python -m pytest --cov=apps.presentations

# Ejecutar tests específicos
docker-compose exec web python -m pytest apps/presentations/tests/test_models.py -v
```

## Estructura del proyecto

```
slidemotion/
├── apps/
│   └── presentations/          # App principal
│       ├── models.py           # Modelos Presentation y Slide
│       ├── views.py            # Vistas y controladores
│       ├── tasks.py            # Tareas Celery
│       ├── services.py         # Lógica de negocio
│       └── tests/              # Suite de tests
│
├── slidemotion/                # Configuración Django
│   ├── settings/               # Settings por entorno
│   └── celery.py               # Configuración Celery
│
├── templates/                  # Templates globales
├── static/                     # Archivos estáticos
├── media/                      # Archivos subidos
├── theme/                      # App Tailwind CSS
│
├── docker-compose.yml          # Desarrollo
├── docker-compose.prod.yml     # Producción
├── Dockerfile                  # Imagen desarrollo
├── Dockerfile.prod            # Imagen producción
└── requirements.txt            # Dependencias Python
```

## Despliegue en producción

### Guía de despliegue en VPS

Para desplegar en tu propio servidor con Traefik y SSL automático:

1. **Preparar el VPS** (Ubuntu 22.04+ recomendado)
   ```bash
   # Instalar Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Instalar Docker Compose
   sudo apt install docker-compose-plugin -y
   ```

2. **Configurar DNS**
   - Apuntar tu dominio al IP del VPS
   - Configurar registros A para tu dominio principal y subdominios

3. **Clonar y configurar**
   ```bash
   git clone https://github.com/tu-usuario/tu-repositorio.git
   cd tu-repositorio

   # Copiar y editar variables de entorno
   cp .env.production.example .env
   nano .env  # Cambiar SECRET_KEY, DOMAIN, passwords, etc.
   ```

4. **Desplegar**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh --first-install
   ```

5. **Verificar**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   docker compose -f docker-compose.prod.yml logs web -f
   ```

### Comandos de producción útiles

```bash
# Ver estado de servicios
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs web --tail=100

# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Actualizar código
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d web

# Backup de base de datos
docker compose -f docker-compose.prod.yml exec db pg_dump -U user database > backup.sql

# Reiniciar servicio
docker compose -f docker-compose.prod.yml restart web
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## Autor

Desarrollado por **José Antonio Olmos**
