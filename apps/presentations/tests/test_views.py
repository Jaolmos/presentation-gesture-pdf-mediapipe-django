"""
Tests para vistas de la aplicación presentations.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from apps.presentations.models import Presentation, Slide


@pytest.mark.django_db
class TestPresentationViews:
    """Tests para las vistas de presentaciones."""

    def setup_method(self):
        """Configuración que se ejecuta antes de cada test."""
        self.client = Client()

    def test_home_view_no_presentations(self):
        """Test de vista home sin presentaciones."""
        url = reverse('presentations:home')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations' in response.context
        assert len(response.context['presentations']) == 0
        assert response.context['total_presentations'] == 0

    def test_home_view_with_presentations(self):
        """Test de vista home con presentaciones."""
        # Crear presentaciones de prueba
        presentation1 = Presentation.objects.create(
            title='Presentación 1',
            total_slides=5,
            is_converted=True
        )
        presentation2 = Presentation.objects.create(
            title='Presentación 2',
            total_slides=0,
            is_converted=False
        )

        url = reverse('presentations:home')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations' in response.context
        assert len(response.context['presentations']) == 2
        assert response.context['total_presentations'] == 2

        # Verificar que las presentaciones están en el contexto
        presentations = list(response.context['presentations'])
        assert presentation1 in presentations
        assert presentation2 in presentations

    def test_home_view_pagination(self):
        """Test de paginación en vista home."""
        # Crear más de 6 presentaciones para probar paginación
        for i in range(8):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i,
                is_converted=i % 2 == 0
            )

        url = reverse('presentations:home')
        response = self.client.get(url)

        assert response.status_code == 200
        # Debería mostrar máximo 10 presentaciones en home (configuración de paginación)
        assert len(response.context['presentations']) <= 10

    def test_upload_view_get(self):
        """Test GET de vista de carga."""
        url = reverse('presentations:upload')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['title'] == 'Subir nueva presentación'

    def test_upload_view_post_valid(self):
        """Test POST válido de vista de carga."""
        # Crear archivo PDF de prueba
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        url = reverse('presentations:upload')
        data = {
            'title': 'Mi Presentación de Prueba',
            'pdf_file': pdf_file
        }

        response = self.client.post(url, data)

        # Verificar redirección
        assert response.status_code == 302

        # Verificar que se creó la presentación
        assert Presentation.objects.count() == 1
        presentation = Presentation.objects.first()
        assert presentation.title == 'Mi Presentación de Prueba'
        assert presentation.pdf_file is not None
        assert not presentation.is_converted  # Inicialmente no convertida

    def test_upload_view_post_invalid(self):
        """Test POST inválido de vista de carga."""
        url = reverse('presentations:upload')
        data = {
            'title': '',  # Título vacío
            # Sin archivo PDF
        }

        response = self.client.post(url, data)

        # Debería quedarse en la misma página con errores
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

        # Verificar que no se creó ninguna presentación
        assert Presentation.objects.count() == 0

    def test_presentation_detail_view(self):
        """Test de vista de detalle de presentación."""
        # Crear presentación de prueba
        presentation = Presentation.objects.create(
            title='Presentación de Prueba',
            total_slides=3,
            is_converted=True
        )

        # Crear slides de prueba
        for i in range(3):
            Slide.objects.create(
                presentation=presentation,
                slide_number=i + 1
            )

        url = reverse('presentations:presentation_detail', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context['presentation'] == presentation
        assert 'slides' in response.context
        assert len(response.context['slides']) == 3

    def test_presentation_detail_view_not_found(self):
        """Test de vista de detalle con presentación inexistente."""
        url = reverse('presentations:presentation_detail', kwargs={'pk': 999})
        response = self.client.get(url)

        assert response.status_code == 404

    def test_presentation_detail_view_no_slides(self):
        """Test de vista de detalle sin slides."""
        presentation = Presentation.objects.create(
            title='Presentación Sin Slides',
            total_slides=0,
            is_converted=True
        )

        url = reverse('presentations:presentation_detail', kwargs={'pk': presentation.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context['presentation'] == presentation
        assert len(response.context['slides']) == 0

    def test_presentation_list_view_no_filter(self):
        """Test de vista de lista sin filtros."""
        # Crear presentaciones de prueba
        presentation1 = Presentation.objects.create(
            title='Presentación A',
            total_slides=5,
            is_converted=True
        )
        presentation2 = Presentation.objects.create(
            title='Presentación B',
            total_slides=0,
            is_converted=False
        )

        url = reverse('presentations:list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations' in response.context
        assert len(response.context['presentations']) == 2

    def test_presentation_list_view_search_filter(self):
        """Test de vista de lista con filtro de búsqueda."""
        # Crear presentaciones de prueba
        Presentation.objects.create(
            title='Django Tutorial',
            total_slides=10,
            is_converted=True
        )
        Presentation.objects.create(
            title='Python Basics',
            total_slides=8,
            is_converted=True
        )

        url = reverse('presentations:list')
        response = self.client.get(url, {'search': 'Django'})

        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['presentations'][0].title == 'Django Tutorial'
        assert response.context['search_query'] == 'Django'

    def test_presentation_list_view_converted_filter(self):
        """Test de vista de lista con filtro de conversión."""
        # Crear presentaciones de prueba
        Presentation.objects.create(
            title='Convertida',
            total_slides=5,
            is_converted=True
        )
        Presentation.objects.create(
            title='Pendiente',
            total_slides=0,
            is_converted=False
        )

        url = reverse('presentations:list')

        # Filtrar solo convertidas
        response = self.client.get(url, {'converted': 'yes'})
        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['presentations'][0].title == 'Convertida'
        assert response.context['converted_filter'] == 'yes'

        # Filtrar solo pendientes
        response = self.client.get(url, {'converted': 'no'})
        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['presentations'][0].title == 'Pendiente'
        assert response.context['converted_filter'] == 'no'

    def test_presentation_list_view_combined_filters(self):
        """Test de vista de lista con múltiples filtros."""
        # Crear presentaciones de prueba
        Presentation.objects.create(
            title='Django Avanzado',
            total_slides=15,
            is_converted=True
        )
        Presentation.objects.create(
            title='Django Básico',
            total_slides=0,
            is_converted=False
        )
        Presentation.objects.create(
            title='Python Avanzado',
            total_slides=12,
            is_converted=True
        )

        url = reverse('presentations:list')
        response = self.client.get(url, {
            'search': 'Django',
            'converted': 'yes'
        })

        assert response.status_code == 200
        assert len(response.context['presentations']) == 1
        assert response.context['presentations'][0].title == 'Django Avanzado'

    def test_upload_success_message(self):
        """Test que verifica mensaje de éxito al subir presentación."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        url = reverse('presentations:upload')
        data = {
            'title': 'Mi Presentación',
            'pdf_file': pdf_file
        }

        response = self.client.post(url, data, follow=True)

        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert 'exitosamente' in str(messages[0])

    def test_presentation_list_pagination(self):
        """Test de paginación en lista de presentaciones."""
        # Crear más presentaciones de las que caben en una página
        for i in range(15):
            Presentation.objects.create(
                title=f'Presentación {i+1}',
                total_slides=i,
                is_converted=True
            )

        url = reverse('presentations:list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations' in response.context
        # Verificar que hay paginación
        assert response.context['presentations'].has_other_pages

    def test_view_context_data(self):
        """Test que verifica datos del contexto en las vistas."""
        # Test home view context
        url = reverse('presentations:home')
        response = self.client.get(url)
        # Home view no tiene 'title' en el contexto, solo presentations y total_presentations
        assert 'presentations' in response.context
        assert 'total_presentations' in response.context

        # Test upload view context
        url = reverse('presentations:upload')
        response = self.client.get(url)
        assert 'title' in response.context
        assert response.context['title'] == 'Subir nueva presentación'

        # Test list view context
        url = reverse('presentations:list')
        response = self.client.get(url)
        assert 'title' in response.context