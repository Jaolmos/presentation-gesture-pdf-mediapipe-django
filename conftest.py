"""
Configuración de pytest para SlideMotion.
Fixtures y configuraciones compartidas para todos los tests.
"""
import os
import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slidemotion.settings')
django.setup()

User = get_user_model()


@pytest.fixture
def user(db):
    """
    Fixture que crea un usuario de prueba.

    Returns:
        User: Usuario autenticado para tests
    """
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """
    Fixture que proporciona un cliente autenticado.

    Args:
        client: Cliente de test de Django
        user: Usuario de prueba

    Returns:
        Client: Cliente autenticado listo para usar
    """
    client.force_login(user)
    return client


@pytest.fixture
def admin_user(db):
    """
    Fixture que crea un usuario administrador.

    Returns:
        User: Usuario administrador para tests
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def admin_client(client, admin_user):
    """
    Fixture que proporciona un cliente autenticado como administrador.

    Args:
        client: Cliente de test de Django
        admin_user: Usuario administrador

    Returns:
        Client: Cliente autenticado como admin
    """
    client.force_login(admin_user)
    return client


@pytest.fixture
def sample_presentation(db):
    """
    Fixture que crea una presentación de prueba con slides y archivos.

    Returns:
        Presentation: Presentación con 3 slides completos
    """
    from apps.presentations.models import Presentation, Slide
    from django.core.files.base import ContentFile
    from PIL import Image
    import io

    # Crear presentación
    presentation = Presentation.objects.create(
        title='Presentación de Prueba',
        total_slides=3,
        is_converted=True,
        processing_status='completed'
    )

    # Crear slides con imágenes simuladas
    for i in range(3):
        # Crear imagen simulada con PIL
        image = Image.new('RGB', (800, 600), color=(100 + i * 50, 50, 150))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        # Crear ContentFile
        image_content = ContentFile(buffer.read(), name=f'slide_{i+1}.png')

        # Crear slide con imagen
        Slide.objects.create(
            presentation=presentation,
            slide_number=i + 1,
            image_file=image_content
        )

    return presentation