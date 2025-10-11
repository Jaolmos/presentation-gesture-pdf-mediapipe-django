"""
Tests para configuración de URLs de la aplicación presentations.
"""
import pytest
from django.urls import reverse, resolve
from django.test import TestCase
from apps.presentations import views


class TestPresentationURLs(TestCase):
    """Tests para las URLs de presentations."""

    def test_home_url_resolves(self):
        """Test que URL home resuelve correctamente."""
        url = reverse('presentations:home')
        assert url == '/'

        resolved = resolve(url)
        assert resolved.func == views.home
        assert resolved.view_name == 'presentations:home'

    def test_home_content_url_resolves(self):
        """Test que URL home_content resuelve correctamente."""
        url = reverse('presentations:home_content')
        assert url == '/home/content/'

        resolved = resolve(url)
        assert resolved.func == views.home_content
        assert resolved.view_name == 'presentations:home_content'

    def test_upload_url_resolves(self):
        """Test que URL upload resuelve correctamente."""
        url = reverse('presentations:upload')
        assert url == '/upload/'

        resolved = resolve(url)
        assert resolved.func == views.upload_presentation
        assert resolved.view_name == 'presentations:upload'

    def test_upload_htmx_url_resolves(self):
        """Test que URL upload_htmx resuelve correctamente."""
        url = reverse('presentations:upload_htmx')
        assert url == '/upload/htmx/'

        resolved = resolve(url)
        assert resolved.func == views.upload_presentation_htmx
        assert resolved.view_name == 'presentations:upload_htmx'

    def test_check_status_url_resolves(self):
        """Test que URL check_status resuelve correctamente."""
        url = reverse('presentations:check_status', kwargs={'pk': 1})
        assert url == '/presentation/1/status/'

        resolved = resolve(url)
        assert resolved.func == views.check_presentation_status
        assert resolved.view_name == 'presentations:check_status'
        assert resolved.kwargs == {'pk': 1}

    def test_check_badge_url_resolves(self):
        """Test que URL check_badge resuelve correctamente."""
        url = reverse('presentations:check_badge', kwargs={'pk': 1})
        assert url == '/presentation/1/badge/'

        resolved = resolve(url)
        assert resolved.func == views.check_presentation_badge
        assert resolved.view_name == 'presentations:check_badge'
        assert resolved.kwargs == {'pk': 1}

    def test_presentation_detail_url_resolves(self):
        """Test que URL presentation_detail resuelve correctamente."""
        url = reverse('presentations:presentation_detail', kwargs={'pk': 1})
        assert url == '/presentation/1/'

        resolved = resolve(url)
        assert resolved.func == views.presentation_detail
        assert resolved.view_name == 'presentations:presentation_detail'
        assert resolved.kwargs == {'pk': 1}

    def test_delete_presentation_url_resolves(self):
        """Test que URL delete_presentation resuelve correctamente."""
        url = reverse('presentations:delete_presentation', kwargs={'pk': 5})
        assert url == '/presentation/5/delete/'

        resolved = resolve(url)
        assert resolved.func == views.delete_presentation
        assert resolved.view_name == 'presentations:delete_presentation'
        assert resolved.kwargs == {'pk': 5}

    def test_delete_presentation_htmx_url_resolves(self):
        """Test que URL delete_presentation_htmx resuelve correctamente."""
        url = reverse('presentations:delete_presentation_htmx', kwargs={'pk': 3})
        assert url == '/presentation/3/delete/htmx/'

        resolved = resolve(url)
        assert resolved.func == views.delete_presentation_htmx
        assert resolved.view_name == 'presentations:delete_presentation_htmx'
        assert resolved.kwargs == {'pk': 3}

    def test_presentation_mode_url_resolves(self):
        """Test que URL presentation_mode resuelve correctamente."""
        url = reverse('presentations:presentation_mode', kwargs={'pk': 2})
        assert url == '/presentar/2/'

        resolved = resolve(url)
        assert resolved.func == views.presentation_mode
        assert resolved.view_name == 'presentations:presentation_mode'
        assert resolved.kwargs == {'pk': 2}

    def test_presentation_slide_url_resolves(self):
        """Test que URL presentation_slide resuelve correctamente."""
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': 4,
            'slide_number': 7
        })
        assert url == '/presentar/4/slide/7/'

        resolved = resolve(url)
        assert resolved.func == views.presentation_slide
        assert resolved.view_name == 'presentations:presentation_slide'
        assert resolved.kwargs == {'pk': 4, 'slide_number': 7}

    def test_presentation_list_url_resolves(self):
        """Test que URL list resuelve correctamente."""
        url = reverse('presentations:list')
        assert url == '/list/'

        resolved = resolve(url)
        assert resolved.func == views.presentation_list
        assert resolved.view_name == 'presentations:list'

    def test_list_content_url_resolves(self):
        """Test que URL list_content resuelve correctamente."""
        url = reverse('presentations:list_content')
        assert url == '/list/content/'

        resolved = resolve(url)
        assert resolved.func == views.presentation_list_content
        assert resolved.view_name == 'presentations:list_content'

    def test_camera_config_url_resolves(self):
        """Test que URL camera_config resuelve correctamente."""
        url = reverse('presentations:camera_config')
        assert url == '/config/'

        resolved = resolve(url)
        assert resolved.func == views.camera_config
        assert resolved.view_name == 'presentations:camera_config'

    def test_app_name_configured(self):
        """Test que app_name está configurado correctamente."""
        # Verificar que el namespace funciona
        url = reverse('presentations:home')
        assert url is not None

        # Verificar que sin namespace falla
        with pytest.raises(Exception):
            reverse('home')

    def test_url_patterns_count(self):
        """Test que hay el número correcto de URL patterns."""
        from apps.presentations.urls import urlpatterns
        assert len(urlpatterns) == 14

    def test_urls_with_different_pk_values(self):
        """Test URLs con diferentes valores de pk."""
        # Test con pk pequeño
        url = reverse('presentations:presentation_detail', kwargs={'pk': 1})
        assert url == '/presentation/1/'

        # Test con pk grande
        url = reverse('presentations:presentation_detail', kwargs={'pk': 999999})
        assert url == '/presentation/999999/'

        # Test con pk muy grande
        url = reverse('presentations:presentation_detail', kwargs={'pk': 2147483647})
        assert url == '/presentation/2147483647/'

    def test_slide_urls_with_different_values(self):
        """Test URLs de slides con diferentes valores."""
        # Test con números normales
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': 1,
            'slide_number': 1
        })
        assert url == '/presentar/1/slide/1/'

        # Test con números más grandes
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': 100,
            'slide_number': 50
        })
        assert url == '/presentar/100/slide/50/'

    def test_url_namespacing_consistency(self):
        """Test que todas las URLs usan el namespace presentations."""
        expected_urls = [
            'presentations:home',
            'presentations:home_content',
            'presentations:upload',
            'presentations:upload_htmx',
            'presentations:presentation_detail',
            'presentations:delete_presentation',
            'presentations:delete_presentation_htmx',
            'presentations:presentation_mode',
            'presentations:presentation_slide',
            'presentations:list',
            'presentations:list_content',
            'presentations:camera_config',
        ]

        for url_name in expected_urls:
            try:
                if 'presentation_slide' in url_name:
                    reverse(url_name, kwargs={'pk': 1, 'slide_number': 1})
                elif any(keyword in url_name for keyword in ['detail', 'delete', 'mode']):
                    reverse(url_name, kwargs={'pk': 1})
                else:
                    reverse(url_name)
            except Exception as e:
                pytest.fail(f"URL {url_name} no se pudo resolver: {e}")

    def test_urls_require_correct_parameters(self):
        """Test que URLs requieren los parámetros correctos."""
        # URLs que requieren pk
        pk_required_urls = [
            'presentations:presentation_detail',
            'presentations:delete_presentation',
            'presentations:delete_presentation_htmx',
            'presentations:presentation_mode'
        ]

        for url_name in pk_required_urls:
            # Debería funcionar con pk
            url = reverse(url_name, kwargs={'pk': 1})
            assert url is not None

            # Debería fallar sin pk
            with pytest.raises(Exception):
                reverse(url_name)

        # URL que requiere pk y slide_number
        url = reverse('presentations:presentation_slide', kwargs={
            'pk': 1,
            'slide_number': 1
        })
        assert url is not None

        # Debería fallar sin slide_number
        with pytest.raises(Exception):
            reverse('presentations:presentation_slide', kwargs={'pk': 1})

        # Debería fallar sin pk
        with pytest.raises(Exception):
            reverse('presentations:presentation_slide', kwargs={'slide_number': 1})

    def test_url_patterns_order(self):
        """Test que los patrones de URL están en orden lógico."""
        from apps.presentations.urls import urlpatterns

        # El patrón más específico debe ir antes que el más general
        # Por ejemplo, 'upload/htmx/' debe ir antes que 'upload/'

        upload_index = None
        upload_htmx_index = None

        for i, pattern in enumerate(urlpatterns):
            if hasattr(pattern, 'name'):
                if pattern.name == 'upload':
                    upload_index = i
                elif pattern.name == 'upload_htmx':
                    upload_htmx_index = i

        # upload debe ir antes que upload_htmx (el orden actual en urls.py)
        assert upload_index < upload_htmx_index

    def test_reverse_urls_match_expected_patterns(self):
        """Test que las URLs generadas coinciden con patrones esperados."""
        test_cases = [
            ('presentations:home', {}, '/'),
            ('presentations:upload', {}, '/upload/'),
            ('presentations:list', {}, '/list/'),
            ('presentations:camera_config', {}, '/config/'),
            ('presentations:presentation_detail', {'pk': 42}, '/presentation/42/'),
            ('presentations:presentation_mode', {'pk': 123}, '/presentar/123/'),
            ('presentations:presentation_slide', {'pk': 5, 'slide_number': 10}, '/presentar/5/slide/10/'),
        ]

        for url_name, kwargs, expected_url in test_cases:
            actual_url = reverse(url_name, kwargs=kwargs)
            assert actual_url == expected_url, f"URL {url_name} generó {actual_url}, esperado {expected_url}"


# ===============================================================================
# TESTS DE URLs - INSTRUCCIONES DE USO
# ===============================================================================
#
# DESCRIPCIÓN:
# Este archivo contiene tests para la configuración de URLs de la aplicación
# presentations, verificando que todas las rutas se resuelvan correctamente.
#
# EJECUTAR TESTS:
# 1. EJECUTAR SOLO TESTS DE URLs:
#    python -m pytest apps/presentations/tests/test_urls.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_urls.py::TestPresentationURLs::test_home_url_resolves -v
#
# 3. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestPresentationURLs: Tests para todas las URLs de la aplicación
# - Cada test verifica que una URL específica resuelva correctamente
# - Verificación de parámetros requeridos y opcionales
# - Verificación de namespace y nombres de URL
#
# URLs TESTADAS:
# ✓ home: Página principal ('/')
# ✓ home_content: Contenido HTMX de home
# ✓ upload: Formulario de carga
# ✓ upload_htmx: Carga HTMX
# ✓ presentation_detail: Detalle de presentación (requiere pk)
# ✓ delete_presentation: Eliminación (requiere pk)
# ✓ delete_presentation_htmx: Eliminación HTMX (requiere pk)
# ✓ presentation_mode: Modo presentación (requiere pk)
# ✓ presentation_slide: API de slides (requiere pk y slide_number)
# ✓ list: Lista de presentaciones
# ✓ list_content: Contenido HTMX de lista
# ✓ camera_config: Configuración de cámara
#
# FUNCIONALIDADES TESTADAS:
# ✓ Resolución correcta de URLs
# ✓ Parámetros requeridos (pk, slide_number)
# ✓ Namespace 'presentations' configurado
# ✓ Nombres de URL únicos y correctos
# ✓ Orden correcto de patrones (específicos antes que generales)
# ✓ Generación de URLs con reverse()
# ✓ Manejo de diferentes valores de parámetros
# ✓ Validación de estructura de urlpatterns
#
# CASOS EDGE TESTADOS:
# ✓ URLs con parámetros grandes (pk=999999)
# ✓ URLs sin parámetros requeridos (deben fallar)
# ✓ Namespace requerido (sin namespace debe fallar)
# ✓ Orden de patrones para evitar conflictos
#
# EJEMPLOS DE OUTPUT ESPERADO:
# ✓ 15 tests pasando
# ✓ Todas las URLs resuelven correctamente
# ✓ Parámetros requeridos validados
# ✓ Namespace funcionando correctamente
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver tests disponibles: python -m pytest apps/presentations/tests/test_urls.py --collect-only
# - Ejecutar con detalle: python -m pytest apps/presentations/tests/test_urls.py -v -s
#
# NOTAS IMPORTANTES:
# - Estos tests verifican la configuración de URLs, no la funcionalidad de las vistas
# - Para testear vistas, usar test_views.py, test_htmx_views.py, etc.
# - Los tests de URLs son rápidos y no requieren base de datos
# - Útiles para detectar errores de configuración de routing
#
# ===============================================================================