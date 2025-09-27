"""
Tests para modo presentación de la aplicación presentations.
"""
import pytest
import json
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.presentations.models import Presentation, Slide


@pytest.mark.django_db
class TestPresentationMode:
    """Tests para el modo de presentación fullscreen."""

    def setup_method(self):
        """Configuración que se ejecuta antes de cada test."""
        self.client = Client()

    def test_presentation_mode_view_success(self):
        """Test de vista de modo presentación exitosa."""
        # Crear presentación convertida
        presentation = Presentation.objects.create(
            title='Presentación de Prueba',
            total_slides=3,
            is_converted=True
        )

        # Crear slides
        slides = []
        for i in range(3):
            slide = Slide.objects.create(
                presentation=presentation,
                slide_number=i + 1
            )
            slides.append(slide)

        url = reverse('presentations:presentation_mode', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations/presentation_mode.html' in [t.name for t in response.templates]

        # Verificar contexto
        assert response.context['presentation'] == presentation
        assert response.context['total_slides'] == 3
        assert response.context['current_slide'] == slides[0]  # Primer slide
        assert response.context['current_slide_number'] == 1
        assert response.context['title'] == f'Presentación: {presentation.title}'

    def test_presentation_mode_view_not_converted(self):
        """Test de vista de modo presentación con presentación no convertida."""
        presentation = Presentation.objects.create(
            title='Presentación No Convertida',
            total_slides=0,
            is_converted=False
        )

        url = reverse('presentations:presentation_mode', kwargs={'pk': presentation.pk})
        response = self.client.get(url, follow=True)

        # Debería redirigir al detalle con mensaje de error
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse('presentations:presentation_detail', kwargs={'pk': presentation.pk})

    def test_presentation_mode_view_no_slides(self):
        """Test de vista de modo presentación sin slides."""
        presentation = Presentation.objects.create(
            title='Presentación Sin Slides',
            total_slides=0,
            is_converted=True  # Marcada como convertida pero sin slides
        )

        url = reverse('presentations:presentation_mode', kwargs={'pk': presentation.pk})
        response = self.client.get(url, follow=True)

        # Debería redirigir al detalle con mensaje de error
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse('presentations:presentation_detail', kwargs={'pk': presentation.pk})

    def test_presentation_mode_view_404(self):
        """Test de vista de modo presentación con presentación inexistente."""
        url = reverse('presentations:presentation_mode', kwargs={'pk': 999})
        response = self.client.get(url)

        assert response.status_code == 404

    def test_presentation_mode_single_slide(self):
        """Test de modo presentación con una sola slide."""
        presentation = Presentation.objects.create(
            title='Presentación Una Slide',
            total_slides=1,
            is_converted=True
        )

        slide = Slide.objects.create(
            presentation=presentation,
            slide_number=1
        )

        url = reverse('presentations:presentation_mode', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context['total_slides'] == 1
        assert response.context['current_slide'] == slide
        assert response.context['current_slide_number'] == 1

    def test_presentation_mode_many_slides(self):
        """Test de modo presentación con muchas slides."""
        presentation = Presentation.objects.create(
            title='Presentación Muchas Slides',
            total_slides=50,
            is_converted=True
        )

        # Crear 50 slides
        slides = []
        for i in range(50):
            slide = Slide.objects.create(
                presentation=presentation,
                slide_number=i + 1
            )
            slides.append(slide)

        url = reverse('presentations:presentation_mode', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context['total_slides'] == 50
        assert response.context['current_slide'] == slides[0]


@pytest.mark.django_db
class TestPresentationSlideAPI:
    """Tests para la API de slides del modo presentación."""

    def setup_method(self):
        """Configuración que se ejecuta antes de cada test."""
        self.client = Client()

        # Crear presentación con slides de prueba
        self.presentation = Presentation.objects.create(
            title='Presentación API Test',
            total_slides=5,
            is_converted=True
        )

        # Crear 5 slides
        self.slides = []
        for i in range(5):
            slide = Slide.objects.create(
                presentation=self.presentation,
                slide_number=i + 1
            )
            self.slides.append(slide)

    def test_presentation_slide_valid_number(self):
        """Test de API de slide con número válido."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 3
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

        data = json.loads(response.content)
        assert data['slide_number'] == 3
        assert data['total_slides'] == 5
        assert data['presentation_title'] == 'Presentación API Test'
        assert data['has_previous'] is True
        assert data['has_next'] is True
        assert 'slide_image_url' in data

    def test_presentation_slide_first_slide(self):
        """Test de API con primera slide."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 1
        })
        response = self.client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['slide_number'] == 1
        assert data['has_previous'] is False
        assert data['has_next'] is True

    def test_presentation_slide_last_slide(self):
        """Test de API con última slide."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 5
        })
        response = self.client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['slide_number'] == 5
        assert data['has_previous'] is True
        assert data['has_next'] is False

    def test_presentation_slide_invalid_number_low(self):
        """Test de API con número de slide demasiado bajo."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 0
        })
        response = self.client.get(url)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
        assert data['error'] == 'Número de slide inválido'
        assert data['current_slide'] == 1
        assert data['total_slides'] == 5

    def test_presentation_slide_invalid_number_high(self):
        """Test de API con número de slide demasiado alto."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 10
        })
        response = self.client.get(url)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
        assert data['error'] == 'Número de slide inválido'

    def test_presentation_slide_negative_number(self):
        """Test de API con número de slide negativo."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': -1
        })
        response = self.client.get(url)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_presentation_slide_presentation_not_found(self):
        """Test de API con presentación inexistente."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': 999,
            'slide_number': 1
        })
        response = self.client.get(url)

        assert response.status_code == 404

    def test_presentation_slide_no_slides(self):
        """Test de API con presentación sin slides."""
        empty_presentation = Presentation.objects.create(
            title='Presentación Vacía',
            total_slides=0,
            is_converted=True
        )

        url = reverse('presentations:presentation_slide', kwargs={
            'pk': empty_presentation.pk,
            'slide_number': 1
        })
        response = self.client.get(url)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['total_slides'] == 0

    def test_presentation_slide_response_structure(self):
        """Test de estructura completa de respuesta de la API."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': self.presentation.pk,
            'slide_number': 2
        })
        response = self.client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)

        # Verificar que todos los campos requeridos están presentes
        required_fields = [
            'slide_image_url',
            'slide_number',
            'total_slides',
            'presentation_title',
            'has_previous',
            'has_next'
        ]

        for field in required_fields:
            assert field in data, f"Campo '{field}' faltante en respuesta"

        # Verificar tipos de datos
        assert isinstance(data['slide_number'], int)
        assert isinstance(data['total_slides'], int)
        assert isinstance(data['presentation_title'], str)
        assert isinstance(data['has_previous'], bool)
        assert isinstance(data['has_next'], bool)
        assert isinstance(data['slide_image_url'], str)

    def test_presentation_slide_single_slide_presentation(self):
        """Test de API con presentación de una sola slide."""
        single_presentation = Presentation.objects.create(
            title='Una Sola Slide',
            total_slides=1,
            is_converted=True
        )

        Slide.objects.create(
            presentation=single_presentation,
            slide_number=1
        )

        url = reverse('presentations:presentation_slide', kwargs={
            'pk': single_presentation.pk,
            'slide_number': 1
        })
        response = self.client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['slide_number'] == 1
        assert data['total_slides'] == 1
        assert data['has_previous'] is False
        assert data['has_next'] is False

    def test_presentation_slide_missing_slide_object(self):
        """Test de API cuando faltan objetos Slide específicos."""
        # Crear presentación que dice tener 3 slides pero solo crear 2
        incomplete_presentation = Presentation.objects.create(
            title='Presentación Incompleta',
            total_slides=3,
            is_converted=True
        )

        # Solo crear 2 slides de los 3 esperados
        Slide.objects.create(presentation=incomplete_presentation, slide_number=1)
        Slide.objects.create(presentation=incomplete_presentation, slide_number=2)

        # Intentar acceder al slide 3 que no existe
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': incomplete_presentation.pk,
            'slide_number': 3
        })
        response = self.client.get(url)

        assert response.status_code == 404
        data = json.loads(response.content)
        assert data['error'] == 'Slide no encontrado'


# ===============================================================================
# TESTS DE MODO PRESENTACIÓN - INSTRUCCIONES DE USO
# ===============================================================================
#
# DESCRIPCIÓN:
# Este archivo contiene tests para el modo de presentación fullscreen y la API
# de navegación de slides que permite control por gestos y teclado.
#
# EJECUTAR TESTS:
# 1. EJECUTAR SOLO TESTS DE MODO PRESENTACIÓN:
#    python -m pytest apps/presentations/tests/test_presentation_mode.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_presentation_mode.py::TestPresentationMode::test_presentation_mode_view_success -v
#
# 3. EJECUTAR SOLO TESTS DE API:
#    python -m pytest apps/presentations/tests/test_presentation_mode.py::TestPresentationSlideAPI -v
#
# 4. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestPresentationMode: Tests para vista de modo presentación fullscreen
# - TestPresentationSlideAPI: Tests para API AJAX de navegación de slides
# - setup_method(): Configuración del cliente y datos de test
# - @pytest.mark.django_db permite acceso a la base de datos
#
# VISTAS TESTADAS:
# ✓ presentation_mode: Vista fullscreen de presentación
# ✓ presentation_slide: API AJAX para cambio de slides
# ✓ Validaciones de estado de presentación
# ✓ Manejo de errores y casos edge
# ✓ Navegación entre slides
#
# FUNCIONALIDADES TESTADAS:
# ✓ Acceso a modo presentación con presentación válida
# ✓ Redirección cuando presentación no está convertida
# ✓ Redirección cuando no hay slides disponibles
# ✓ API JSON para navegación de slides
# ✓ Validación de números de slide
# ✓ Información de navegación (anterior/siguiente)
# ✓ Manejo de presentaciones con una sola slide
# ✓ Manejo de presentaciones con muchas slides
# ✓ Respuestas de error estructuradas
#
# CASOS EDGE TESTADOS:
# ✓ Presentación inexistente (404)
# ✓ Números de slide inválidos (0, negativos, muy altos)
# ✓ Presentaciones sin slides
# ✓ Slides faltantes en base de datos
# ✓ Estructura de respuesta JSON completa
#
# EJEMPLOS DE OUTPUT ESPERADO:
# ✓ 18 tests pasando
# ✓ Verificación de vista fullscreen correcta
# ✓ Verificación de API JSON funcionando
# ✓ Verificación de navegación de slides
# ✓ Verificación de manejo de errores
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver tests disponibles: python -m pytest apps/presentations/tests/test_presentation_mode.py --collect-only
# - Ejecutar con detalle: python -m pytest apps/presentations/tests/test_presentation_mode.py -v -s
# - Ejecutar solo tests que fallan: python -m pytest apps/presentations/tests/test_presentation_mode.py --lf
#
# NOTAS IMPORTANTES:
# - Estos tests cubren la lógica de backend del modo presentación
# - La funcionalidad de gestos y teclado se testea en frontend (JavaScript)
# - Los tests de integración completa requieren herramientas E2E
# - La API está diseñada para ser consumida por AJAX/fetch en frontend
#
# ===============================================================================