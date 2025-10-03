"""
Tests para vistas HTMX de la aplicación presentations.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.presentations.models import Presentation, Slide


@pytest.mark.django_db
class TestHTMXViews:
    """Tests para las vistas HTMX."""

    @pytest.fixture(autouse=True)
    def setup(self, authenticated_client):
        """Configuración que se ejecuta antes de cada test."""
        self.client = authenticated_client

    def test_upload_presentation_htmx_get(self):
        """Test GET de vista HTMX de carga - devolver formulario limpio."""
        url = reverse('presentations:upload_htmx')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['success'] is None
        assert 'presentations/partials/upload_form.html' in [t.name for t in response.templates]

    def test_upload_presentation_htmx_post_valid(self):
        """Test POST válido de vista HTMX de carga."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        url = reverse('presentations:upload_htmx')
        data = {
            'title': 'Mi Presentación HTMX',
            'pdf_file': pdf_file
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert 'presentations/partials/upload_result.html' in [t.name for t in response.templates]
        assert response.context['success'] is True
        assert 'presentation' in response.context
        assert 'Mi Presentación HTMX' in response.context['message']

        # Verificar que se creó la presentación
        assert Presentation.objects.count() == 1
        presentation = Presentation.objects.first()
        assert presentation.title == 'Mi Presentación HTMX'

    def test_upload_presentation_htmx_post_invalid(self):
        """Test POST inválido de vista HTMX de carga."""
        url = reverse('presentations:upload_htmx')
        data = {
            'title': '',  # Título vacío
            # Sin archivo PDF
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert 'presentations/partials/upload_form.html' in [t.name for t in response.templates]
        assert response.context['success'] is False
        assert 'form' in response.context
        assert response.context['form'].errors

        # Verificar que no se creó ninguna presentación
        assert Presentation.objects.count() == 0

    def test_upload_presentation_htmx_conversion_error(self):
        """Test de vista HTMX con error en conversión."""
        # Crear archivo PDF corrupto
        corrupted_pdf = SimpleUploadedFile(
            "corrupted.pdf",
            b'not a real pdf content',
            content_type="application/pdf"
        )

        url = reverse('presentations:upload_htmx')
        data = {
            'title': 'PDF Corrupto',
            'pdf_file': corrupted_pdf
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert response.context['success'] is True
        # Con procesamiento asíncrono Celery, el status es 'info' porque la carga es exitosa
        # La conversión fallará luego en el worker de Celery
        assert response.context['status'] == 'info'
        assert 'procesamiento' in response.context['message'].lower() or 'cargada' in response.context['message'].lower()

    def test_home_content_view_no_presentations(self):
        """Test de vista HTMX de contenido home sin presentaciones."""
        url = reverse('presentations:home_content')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations/partials/home_content.html' in [t.name for t in response.templates]
        assert 'presentations' in response.context
        assert len(response.context['presentations']) == 0
        assert response.context['total_presentations'] == 0

    def test_home_content_view_with_presentations(self):
        """Test de vista HTMX de contenido home con presentaciones."""
        # Crear presentaciones de prueba
        for i in range(3):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i+1,
                is_converted=True
            )

        url = reverse('presentations:home_content')
        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.context['presentations']) == 3
        assert response.context['total_presentations'] == 3

    def test_home_content_view_pagination(self):
        """Test de paginación en vista HTMX de contenido home."""
        # Crear más de 10 presentaciones para probar paginación
        for i in range(12):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i+1,
                is_converted=True
            )

        url = reverse('presentations:home_content')
        response = self.client.get(url)

        assert response.status_code == 200
        # Debería mostrar máximo 10 presentaciones por página
        assert len(response.context['presentations']) == 10
        assert response.context['presentations'].has_other_pages

        # Test segunda página
        response = self.client.get(url, {'page': 2})
        assert response.status_code == 200
        assert len(response.context['presentations']) == 2

    def test_presentation_list_content_view_no_filter(self):
        """Test de vista HTMX de contenido lista sin filtros."""
        # Crear presentaciones de prueba
        for i in range(5):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i+1,
                is_converted=i % 2 == 0
            )

        url = reverse('presentations:list_content')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations/partials/list_content.html' in [t.name for t in response.templates]
        assert len(response.context['presentations']) == 5

    def test_presentation_list_content_view_search_filter(self):
        """Test de vista HTMX de contenido lista con filtro de búsqueda."""
        # Crear presentaciones de prueba
        Presentation.objects.create(title='Django Tutorial', total_slides=10, is_converted=True)
        Presentation.objects.create(title='Python Basics', total_slides=8, is_converted=True)
        Presentation.objects.create(title='Django Advanced', total_slides=12, is_converted=False)

        url = reverse('presentations:list_content')
        response = self.client.get(url, {'search': 'Django'})

        assert response.status_code == 200
        assert len(response.context['presentations']) == 2
        assert response.context['search_query'] == 'Django'

    def test_presentation_list_content_view_converted_filter(self):
        """Test de vista HTMX de contenido lista con filtro de conversión."""
        # Crear presentaciones de prueba
        Presentation.objects.create(title='Convertida 1', total_slides=5, is_converted=True)
        Presentation.objects.create(title='Convertida 2', total_slides=3, is_converted=True)
        Presentation.objects.create(title='Pendiente 1', total_slides=0, is_converted=False)

        url = reverse('presentations:list_content')

        # Filtrar solo convertidas
        response = self.client.get(url, {'converted': 'yes'})
        assert response.status_code == 200
        assert len(response.context['presentations']) == 2
        assert response.context['converted_filter'] == 'yes'

        # Filtrar solo pendientes
        response = self.client.get(url, {'converted': 'no'})
        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['converted_filter'] == 'no'

    def test_presentation_list_content_view_combined_filters(self):
        """Test de vista HTMX con múltiples filtros combinados."""
        # Crear presentaciones de prueba
        Presentation.objects.create(title='Django Avanzado', total_slides=15, is_converted=True)
        Presentation.objects.create(title='Django Básico', total_slides=0, is_converted=False)
        Presentation.objects.create(title='Python Avanzado', total_slides=12, is_converted=True)

        url = reverse('presentations:list_content')
        response = self.client.get(url, {
            'search': 'Django',
            'converted': 'yes'
        })

        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['presentations'][0].title == 'Django Avanzado'

    def test_presentation_list_content_pagination(self):
        """Test de paginación en vista HTMX de lista."""
        # Crear más presentaciones de las que caben en una página
        for i in range(15):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i,
                is_converted=True
            )

        url = reverse('presentations:list_content')
        response = self.client.get(url)

        assert response.status_code == 200
        # Verificar que hay paginación (12 por página)
        assert len(response.context['presentations']) == 12
        assert response.context['presentations'].has_other_pages

    def test_delete_presentation_htmx_get(self):
        """Test GET de vista HTMX de eliminación - mostrar confirmación."""
        presentation = Presentation.objects.create(
            title='Presentación a eliminar',
            total_slides=5,
            is_converted=True
        )

        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations/partials/delete_confirm_content.html' in [t.name for t in response.templates]
        assert 'presentation' in response.context
        assert response.context['presentation'] == presentation

    def test_delete_presentation_htmx_post_success(self):
        """Test POST de vista HTMX de eliminación - eliminar exitosamente."""
        presentation = Presentation.objects.create(
            title='Presentación a eliminar',
            total_slides=3,
            is_converted=True
        )
        presentation_id = presentation.pk
        presentation_title = presentation.title

        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': presentation.pk})
        response = self.client.post(url)

        assert response.status_code == 200
        assert 'presentations/partials/delete_result.html' in [t.name for t in response.templates]
        assert response.context['success'] is True
        assert presentation_title in response.context['message']

        # Verificar que la presentación fue eliminada
        assert not Presentation.objects.filter(pk=presentation_id).exists()

    def test_delete_presentation_htmx_post_error(self):
        """Test POST de vista HTMX con error en eliminación."""
        presentation = Presentation.objects.create(
            title='Presentación con error',
            total_slides=2,
            is_converted=True
        )

        # Simular error eliminando el objeto antes de la vista
        presentation_pk = presentation.pk
        presentation.delete()

        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': presentation_pk})
        response = self.client.post(url)

        # Debería retornar 404 porque la presentación ya no existe
        assert response.status_code == 404

    def test_delete_presentation_htmx_404(self):
        """Test de vista HTMX de eliminación con presentación inexistente."""
        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': 999})

        # GET debería devolver 404
        response = self.client.get(url)
        assert response.status_code == 404

        # POST también debería devolver 404
        response = self.client.post(url)
        assert response.status_code == 404

    def test_delete_presentation_htmx_with_slides(self):
        """Test de eliminación HTMX de presentación con slides."""
        presentation = Presentation.objects.create(
            title='Presentación con slides',
            total_slides=3,
            is_converted=True
        )

        # Crear slides (sin archivos reales para tests)
        for i in range(3):
            Slide.objects.create(
                presentation=presentation,
                slide_number=i + 1
            )

        assert presentation.slides.count() == 3

        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': presentation.pk})
        response = self.client.post(url)

        assert response.status_code == 200
        assert response.context['success'] is True

        # Verificar que presentación y slides fueron eliminados
        assert not Presentation.objects.filter(pk=presentation.pk).exists()
        assert Slide.objects.filter(presentation=presentation).count() == 0


# ===============================================================================
# TESTS DE VISTAS HTMX - INSTRUCCIONES DE USO
# ===============================================================================
#
# DESCRIPCIÓN:
# Este archivo contiene tests para todas las vistas HTMX de la aplicación
# presentations que manejan contenido dinámico y actualizaciones asíncronas.
#
# EJECUTAR TESTS:
# 1. EJECUTAR SOLO TESTS DE VISTAS HTMX:
#    python -m pytest apps/presentations/tests/test_htmx_views.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_htmx_views.py::TestHTMXViews::test_upload_presentation_htmx_post_valid -v
#
# 3. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestHTMXViews: Tests para todas las vistas HTMX
# - setup_method(): Configuración del cliente de test antes de cada test
# - @pytest.mark.django_db permite acceso a la base de datos
#
# VISTAS HTMX TESTADAS:
# ✓ upload_presentation_htmx: GET y POST con validación y conversión
# ✓ home_content: Contenido dinámico de home con paginación
# ✓ presentation_list_content: Lista con filtros y búsqueda
# ✓ delete_presentation_htmx: Eliminación con confirmación
# ✓ Manejo de errores y casos edge
# ✓ Templates parciales correctos
#
# FUNCIONALIDADES TESTADAS:
# ✓ Respuestas HTMX con templates parciales
# ✓ Contexto específico para cada vista
# ✓ Filtros y búsqueda dinámica
# ✓ Paginación en contenido HTMX
# ✓ Manejo de errores de conversión PDF
# ✓ Eliminación con confirmación HTMX
# ✓ Estados de éxito y error diferenciados
#
# EJEMPLOS DE OUTPUT ESPERADO:
# ✓ 17 tests pasando
# ✓ Verificación de templates parciales
# ✓ Verificación de contexto HTMX
# ✓ Verificación de funcionalidad asíncrona
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver tests disponibles: python -m pytest apps/presentations/tests/test_htmx_views.py --collect-only
# - Ejecutar con detalle: python -m pytest apps/presentations/tests/test_htmx_views.py -v -s
#
# ===============================================================================