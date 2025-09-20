"""
Tests para servicios de procesamiento de PDFs.
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.presentations.models import Presentation, Slide
from apps.presentations.services import PDFProcessor, PDFConversionError


@pytest.mark.django_db
class TestPDFProcessor:
    """Tests para el servicio PDFProcessor."""

    def setup_method(self):
        """Configuración para cada test."""
        # Crear directorio temporal para tests
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Limpieza después de cada test."""
        # Limpiar archivos temporales si existen
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_convert_pdf_to_images_sin_archivo(self):
        """Test que verifica error cuando no hay archivo PDF."""
        presentation = Presentation.objects.create(
            title="Sin PDF",
            pdf_file=None
        )

        with pytest.raises(PDFConversionError) as exc_info:
            PDFProcessor.convert_pdf_to_images(presentation)

        assert "no tiene archivo PDF asociado" in str(exc_info.value)

    @patch('apps.presentations.services.convert_from_path')
    @patch('apps.presentations.services.os.path.exists')
    def test_convert_pdf_to_images_archivo_inexistente(self, mock_exists, mock_convert):
        """Test que verifica error cuando el archivo PDF no existe."""
        mock_exists.return_value = False

        # Crear presentación con archivo simulado
        pdf_content = b'%PDF-1.4\nfake pdf content'
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        presentation = Presentation.objects.create(
            title="PDF Inexistente",
            pdf_file=pdf_file
        )

        with pytest.raises(PDFConversionError) as exc_info:
            PDFProcessor.convert_pdf_to_images(presentation)

        assert "Archivo PDF no encontrado" in str(exc_info.value)

    @patch('apps.presentations.services.convert_from_path')
    @patch('apps.presentations.services.os.path.exists')
    def test_convert_pdf_to_images_exitoso(self, mock_exists, mock_convert):
        """Test de conversión exitosa de PDF a imágenes."""
        mock_exists.return_value = True

        # Crear imágenes simuladas
        mock_image1 = MagicMock(spec=Image.Image)
        mock_image1.size = (800, 600)
        mock_image1.mode = 'RGB'

        mock_image2 = MagicMock(spec=Image.Image)
        mock_image2.size = (800, 600)
        mock_image2.mode = 'RGB'

        mock_convert.return_value = [mock_image1, mock_image2]

        # Mock para optimización de imágenes
        with patch.object(PDFProcessor, '_optimize_image', side_effect=lambda x: x), \
             patch.object(PDFProcessor, '_image_to_bytes', return_value=b'fake_image_data'):

            # Crear presentación
            pdf_content = b'%PDF-1.4\nfake pdf content'
            pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

            presentation = Presentation.objects.create(
                title="Test PDF",
                pdf_file=pdf_file
            )

            # Ejecutar conversión
            slides = PDFProcessor.convert_pdf_to_images(presentation)

            # Verificar resultados
            assert len(slides) == 2
            assert all(isinstance(slide, Slide) for slide in slides)

            # Verificar que la presentación se actualizó
            presentation.refresh_from_db()
            assert presentation.total_slides == 2
            assert presentation.is_converted is True

            # Verificar que se crearon los slides en la BD
            assert presentation.slides.count() == 2
            assert presentation.slides.filter(slide_number=1).exists()
            assert presentation.slides.filter(slide_number=2).exists()

    def test_optimize_image_no_redimensionar(self):
        """Test que verifica que imágenes pequeñas no se redimensionan."""
        # Crear imagen pequeña simulada
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (800, 600)  # Menor que MAX_WIDTH y MAX_HEIGHT

        result = PDFProcessor._optimize_image(mock_image)

        # Debe devolver la misma imagen sin redimensionar
        assert result == mock_image
        mock_image.resize.assert_not_called()

    def test_optimize_image_redimensionar(self):
        """Test que verifica redimensionamiento de imágenes grandes."""
        # Crear imagen grande simulada
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (2400, 1800)  # Mayor que MAX_WIDTH y MAX_HEIGHT

        # Mock del método resize
        resized_image = MagicMock(spec=Image.Image)
        mock_image.resize.return_value = resized_image

        result = PDFProcessor._optimize_image(mock_image)

        # Verificar que se llamó resize
        mock_image.resize.assert_called_once()

        # Verificar que se calcularon las dimensiones correctas
        call_args = mock_image.resize.call_args[0]
        new_width, new_height = call_args[0]

        # Verificar que las nuevas dimensiones respetan los límites
        assert new_width <= PDFProcessor.MAX_WIDTH
        assert new_height <= PDFProcessor.MAX_HEIGHT

        # Verificar que se mantuvo la proporción aproximadamente
        original_ratio = 2400 / 1800
        new_ratio = new_width / new_height
        assert abs(original_ratio - new_ratio) < 0.01

        assert result == resized_image

    def test_image_to_bytes(self):
        """Test de conversión de imagen PIL a bytes."""
        # Crear imagen real pequeña para testing
        image = Image.new('RGB', (100, 100), color='red')

        result = PDFProcessor._image_to_bytes(image)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_image_to_bytes_conversion_mode(self):
        """Test que verifica conversión de modo de imagen."""
        # Crear imagen en modo no-RGB
        image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))

        with patch.object(image, 'convert') as mock_convert:
            mock_convert.return_value = image

            PDFProcessor._image_to_bytes(image)

            # Verificar que se llamó convert a RGB
            mock_convert.assert_called_once_with('RGB')

    @patch('apps.presentations.services.convert_from_path')
    @patch('apps.presentations.services.os.path.exists')
    def test_convert_pdf_error_en_conversion(self, mock_exists, mock_convert):
        """Test que verifica manejo de errores durante la conversión."""
        mock_exists.return_value = True
        mock_convert.side_effect = Exception("Error en pdf2image")

        pdf_content = b'%PDF-1.4\nfake pdf content'
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        presentation = Presentation.objects.create(
            title="PDF con Error",
            pdf_file=pdf_file
        )

        with pytest.raises(PDFConversionError) as exc_info:
            PDFProcessor.convert_pdf_to_images(presentation)

        assert "Error al convertir PDF" in str(exc_info.value)

    def test_get_conversion_status(self):
        """Test del método de estado de conversión."""
        # Crear presentación con PDF
        pdf_content = b'%PDF-1.4\nfake pdf content'
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        presentation = Presentation.objects.create(
            title="Test Status",
            pdf_file=pdf_file,
            total_slides=3,
            is_converted=True
        )

        # Crear algunos slides
        Slide.objects.create(presentation=presentation, slide_number=1)
        Slide.objects.create(presentation=presentation, slide_number=2)

        status = PDFProcessor.get_conversion_status(presentation)

        assert status['is_converted'] is True
        assert status['total_slides'] == 3
        assert status['slides_count'] == 2
        assert status['has_pdf'] is True
        assert status['pdf_filename'].startswith('test') and status['pdf_filename'].endswith('.pdf')
        assert status['pdf_size_mb'] >= 0  # El archivo puede ser muy pequeño en tests

    def test_get_conversion_status_sin_pdf(self):
        """Test del estado de conversión sin archivo PDF."""
        presentation = Presentation.objects.create(
            title="Sin PDF",
            pdf_file=None
        )

        status = PDFProcessor.get_conversion_status(presentation)

        assert status['is_converted'] is False
        assert status['total_slides'] == 0
        assert status['slides_count'] == 0
        assert status['has_pdf'] is False
        assert status['pdf_filename'] == ''
        assert status['pdf_size_mb'] == 0

    @patch('apps.presentations.services.convert_from_path')
    @patch('apps.presentations.services.os.path.exists')
    def test_create_slides_elimina_existentes(self, mock_exists, mock_convert):
        """Test que verifica que se eliminan slides existentes antes de crear nuevos."""
        mock_exists.return_value = True

        # Crear imagen simulada
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (800, 600)
        mock_image.mode = 'RGB'
        mock_convert.return_value = [mock_image]

        # Crear presentación con slides existentes
        pdf_content = b'%PDF-1.4\nfake pdf content'
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        presentation = Presentation.objects.create(
            title="Con Slides Existentes",
            pdf_file=pdf_file
        )

        # Crear slides existentes
        old_slide1 = Slide.objects.create(presentation=presentation, slide_number=1)
        old_slide2 = Slide.objects.create(presentation=presentation, slide_number=2)

        assert presentation.slides.count() == 2

        with patch.object(PDFProcessor, '_optimize_image', side_effect=lambda x: x), \
             patch.object(PDFProcessor, '_image_to_bytes', return_value=b'fake_image_data'):

            # Ejecutar conversión
            slides = PDFProcessor.convert_pdf_to_images(presentation)

            # Verificar que se eliminaron los slides antiguos y se creó uno nuevo
            assert len(slides) == 1
            assert presentation.slides.count() == 1

            # Verificar que los slides antiguos ya no existen
            assert not Slide.objects.filter(id=old_slide1.id).exists()
            assert not Slide.objects.filter(id=old_slide2.id).exists()


# ===============================================================================
# TESTS DE SERVICIOS PDF - INSTRUCCIONES DE USO
# ===============================================================================
#
# DESCRIPCIÓN:
# Este archivo contiene tests para el servicio PDFProcessor que maneja
# la conversión de archivos PDF a imágenes individuales de slides.
#
# EJECUTAR TESTS:
# 1. EJECUTAR SOLO TESTS DE SERVICIOS:
#    python -m pytest apps/presentations/tests/test_services.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_services.py::TestPDFProcessor::test_convert_pdf_to_images_exitoso -v
#
# 3. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestPDFProcessor: Tests para el servicio de conversión PDF
# - setup_method/teardown_method: Configuración y limpieza por test
# - @pytest.mark.django_db permite acceso a la base de datos
# - Uso extensivo de mocks para simular pdf2image y PIL
#
# FUNCIONALIDADES TESTADAS:
# ✓ Conversión exitosa de PDF a múltiples slides
# ✓ Manejo de errores (archivo inexistente, conversión fallida)
# ✓ Optimización de imágenes (redimensionamiento)
# ✓ Conversión de formatos de imagen
# ✓ Estado de conversión y metadata
# ✓ Eliminación de slides existentes antes de crear nuevos
# ✓ Integración con modelos Django (Presentation, Slide)
#
# MOCKS UTILIZADOS:
# - convert_from_path: Simula pdf2image
# - PIL.Image: Simula objetos de imagen
# - os.path.exists: Simula existencia de archivos
# - Métodos internos del PDFProcessor
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver tests con más detalle: python -m pytest apps/presentations/tests/test_services.py -v -s
# - Ejecutar con coverage: python -m pytest apps/presentations/tests/test_services.py --cov=apps.presentations.services
#
# ===============================================================================