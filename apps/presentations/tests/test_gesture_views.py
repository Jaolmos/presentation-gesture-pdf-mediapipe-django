"""
Tests para vistas de configuración de gestos.
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestGestureViews:
    """Tests para las vistas de configuración de gestos."""

    def setup_method(self):
        """Configuración que se ejecuta antes de cada test."""
        self.client = Client()

    def test_camera_config_view_get(self):
        """Test GET de vista de configuración de cámara."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'title' in response.context
        assert response.context['title'] == 'Configuración de Cámara y Gestos'

    def test_camera_config_view_template(self):
        """Test que verifica el template correcto."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        assert response.status_code == 200
        assert 'presentations/camera_config.html' in [t.name for t in response.templates]

    def test_camera_config_view_contains_elements(self):
        """Test que verifica elementos necesarios en la página."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()

        # Verificar elementos de UI principales
        assert 'cameraSelect' in content
        assert 'sensitivity' in content
        assert 'startCameraBtn' in content
        assert 'stopCameraBtn' in content
        assert 'testGesturesBtn' in content
        assert 'cameraVideo' in content
        assert 'poseCanvas' in content

    def test_camera_config_includes_mediapipe_script(self):
        """Test que verifica inclusión del script de MediaPipe."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()
        assert 'mediapipe/tasks-vision' in content
        assert 'skypack.dev' in content

    def test_camera_config_includes_gesture_detection_script(self):
        """Test que verifica inclusión del script de detección de gestos."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()
        assert 'gesture_detection.js' in content

    def test_camera_config_contains_gesture_descriptions(self):
        """Test que verifica información de gestos disponibles."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()
        assert 'Brazo derecho levantado' in content
        assert 'Brazo izquierdo levantado' in content
        assert 'Siguiente slide' in content
        assert 'Slide anterior' in content

    def test_camera_config_navigation_links(self):
        """Test que verifica enlaces de navegación."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()
        assert 'href="/"' in content  # Link a home
        assert 'Volver' in content

    def test_camera_config_javascript_variables(self):
        """Test que verifica variables JavaScript necesarias."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()
        assert 'gestureDetector' in content
        assert 'cameraManager' in content
        assert 'cameraConfig' in content
        assert 'GestureDetector' in content
        assert 'CameraManager' in content
        assert 'CameraConfig' in content

    def test_camera_config_ui_elements(self):
        """Test que verifica elementos de UI específicos."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()

        # Verificar controles de configuración
        assert 'Seleccionar Cámara' in content
        assert 'Sensibilidad de Detección' in content
        assert 'Iniciar Cámara' in content
        assert 'Detener Cámara' in content
        assert 'Probar Gestos' in content

        # Verificar elementos de estado
        assert 'Estado Actual' in content
        assert 'Vista Previa de Cámara' in content
        assert 'Último gesto' in content

    def test_camera_config_accessibility(self):
        """Test que verifica elementos de accesibilidad."""
        url = reverse('presentations:camera_config')
        response = self.client.get(url)

        content = response.content.decode()

        # Verificar labels y estructura semántica
        assert 'for="cameraSelect"' in content
        assert 'for="sensitivity"' in content
        assert 'label' in content  # Elementos de label presentes


# ===============================================================================
# TESTS DE VISTAS DE GESTOS - INSTRUCCIONES DE USO
# ===============================================================================
#
# DESCRIPCIÓN:
# Este archivo contiene tests para la vista de configuración de cámara y gestos.
# Verifica que la interfaz de configuración se renderice correctamente y contenga
# todos los elementos necesarios para la detección de gestos.
#
# EJECUTAR TESTS:
# 1. EJECUTAR SOLO TESTS DE GESTOS:
#    python -m pytest apps/presentations/tests/test_gesture_views.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_gesture_views.py::TestGestureViews::test_camera_config_view_get -v
#
# 3. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestGestureViews: Tests para vista de configuración de cámara
# - setup_method(): Configuración del cliente de test antes de cada test
# - @pytest.mark.django_db permite acceso a la base de datos
#
# VISTAS TESTADAS:
# ✓ camera_config: GET (mostrar interfaz de configuración)
# ✓ Verificación de template correcto
# ✓ Verificación de elementos de UI
# ✓ Verificación de scripts de MediaPipe y detección
# ✓ Verificación de información de gestos
# ✓ Verificación de navegación
# ✓ Verificación de variables JavaScript
# ✓ Verificación de accesibilidad básica
#
# FUNCIONALIDADES TESTADAS:
# ✓ Renderizado correcto de la vista (200)
# ✓ Contexto de template (título)
# ✓ Inclusión de scripts necesarios (MediaPipe, gesture_detection.js)
# ✓ Elementos de interfaz (selects, botones, canvas, video)
# ✓ Información de gestos disponibles
# ✓ Variables JavaScript necesarias
# ✓ Estructura semántica y accesibilidad
#
# EJEMPLOS DE OUTPUT ESPERADO:
# ✓ 10 tests pasando
# ✓ Verificación de que la página de configuración se carga correctamente
# ✓ Verificación de que todos los elementos necesarios están presentes
# ✓ Verificación de que los scripts de detección están incluidos
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver qué tests existen: python -m pytest apps/presentations/tests/test_gesture_views.py --collect-only
# - Ejecutar tests con salida detallada: python -m pytest apps/presentations/tests/test_gesture_views.py -v -s
# - Ejecutar solo tests que fallan: python -m pytest apps/presentations/tests/test_gesture_views.py --lf
#
# NOTAS IMPORTANTES:
# - Estos tests verifican la interfaz y estructura, no la funcionalidad JavaScript
# - La detección real de gestos se testea en navegador con cámara real
# - Los tests de MediaPipe requieren integración en tiempo real
# - Para tests completos, usar herramientas de testing E2E como Selenium
#
# ===============================================================================