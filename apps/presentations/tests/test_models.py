import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from apps.presentations.models import Presentation, Slide


@pytest.mark.django_db
class TestPresentationModel:
    """Tests para el modelo Presentation"""

    def test_create_presentation(self):
        """Test crear una presentación básica"""
        presentation = Presentation.objects.create(
            title="Mi Presentación de Prueba"
        )

        assert presentation.title == "Mi Presentación de Prueba"
        assert presentation.total_slides == 0
        assert presentation.is_converted is False
        assert presentation.created_at is not None
        assert presentation.updated_at is not None

    def test_presentation_str_method(self):
        """Test método __str__ del modelo"""
        presentation = Presentation.objects.create(
            title="Presentación de Django"
        )

        assert str(presentation) == "Presentación de Django"

    def test_presentation_ordering(self):
        """Test que las presentaciones tienen ordering por fecha de creación"""
        # Verificar que el Meta.ordering está configurado
        assert Presentation._meta.ordering == ['-created_at']

    def test_file_size_mb_property_without_file(self):
        """Test propiedad file_size_mb sin archivo"""
        presentation = Presentation.objects.create(title="Sin archivo")
        assert presentation.file_size_mb == 0

    def test_get_filename_without_file(self):
        """Test método get_filename sin archivo"""
        presentation = Presentation.objects.create(title="Sin archivo")
        assert presentation.get_filename() == ""

    def test_pdf_file_validation(self):
        """Test validación de extensión de archivo PDF"""
        # Crear un archivo simulado con extensión incorrecta
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"file content",
            content_type="text/plain"
        )

        presentation = Presentation(
            title="Test",
            pdf_file=invalid_file
        )

        # Verificar que la validación falla
        with pytest.raises(ValidationError):
            presentation.full_clean()

    def test_verbose_names(self):
        """Test nombres verbose del modelo"""
        assert Presentation._meta.verbose_name == "Presentación"
        assert Presentation._meta.verbose_name_plural == "Presentaciones"


@pytest.mark.django_db
class TestSlideModel:
    """Tests para el modelo Slide"""

    def test_create_slide(self):
        """Test crear un slide básico"""
        presentation = Presentation.objects.create(title="Test Presentation")

        slide = Slide.objects.create(
            presentation=presentation,
            slide_number=1
        )

        assert slide.presentation == presentation
        assert slide.slide_number == 1
        assert slide.created_at is not None

    def test_slide_str_method(self):
        """Test método __str__ del modelo Slide"""
        presentation = Presentation.objects.create(title="Mi Presentación")
        slide = Slide.objects.create(
            presentation=presentation,
            slide_number=3
        )

        assert str(slide) == "Mi Presentación - Slide 3"

    def test_slide_ordering(self):
        """Test que los slides tienen ordering configurado"""
        # Verificar que el Meta.ordering está configurado correctamente
        assert Slide._meta.ordering == ['presentation', 'slide_number']

    def test_unique_together_constraint(self):
        """Test constraintç unique_together para presentation y slide_number"""
        presentation = Presentation.objects.create(title="Test")

        # Crear primer slide
        Slide.objects.create(presentation=presentation, slide_number=1)

        # Intentar crear otro slide con el mismo número debe fallar
        with pytest.raises(Exception):  # IntegrityError en base de datos real
            Slide.objects.create(presentation=presentation, slide_number=1)

    def test_related_name_slides(self):
        """Test que el related_name 'slides' funciona correctamente"""
        presentation = Presentation.objects.create(title="Test")

        slide1 = Slide.objects.create(presentation=presentation, slide_number=1)
        slide2 = Slide.objects.create(presentation=presentation, slide_number=2)

        # Verificar que podemos acceder a los slides desde la presentación
        slides = list(presentation.slides.all())
        assert len(slides) == 2
        assert slide1 in slides
        assert slide2 in slides

    def test_cascade_delete(self):
        """Test que al eliminar una presentación se eliminan sus slides"""
        presentation = Presentation.objects.create(title="Test")

        Slide.objects.create(presentation=presentation, slide_number=1)
        Slide.objects.create(presentation=presentation, slide_number=2)

        # Verificar que hay 2 slides
        assert Slide.objects.filter(presentation=presentation).count() == 2

        # Eliminar la presentación
        presentation.delete()

        # Verificar que no quedan slides
        assert Slide.objects.count() == 0

    def test_image_size_mb_property_without_file(self):
        """Test propiedad image_size_mb sin archivo"""
        presentation = Presentation.objects.create(title="Test")
        slide = Slide.objects.create(presentation=presentation, slide_number=1)

        assert slide.image_size_mb == 0

    def test_verbose_names(self):
        """Test nombres verbose del modelo Slide"""
        assert Slide._meta.verbose_name == "Slide"
        assert Slide._meta.verbose_name_plural == "Slides"


# ===============================================================================
# TUTORIAL RÁPIDO - Cómo usar estos tests:
# ===============================================================================
#
# 1. EJECUTAR TODOS LOS TESTS:
#    python -m pytest apps/presentations/tests/test_models.py -v
#
# 2. EJECUTAR UN TEST ESPECÍFICO:
#    python -m pytest apps/presentations/tests/test_models.py::TestPresentationModel::test_create_presentation -v
#
# 3. EJECUTAR TESTS DE UNA CLASE:
#    python -m pytest apps/presentations/tests/test_models.py::TestPresentationModel -v
#
# 4. EJECUTAR CON COVERAGE:
#    python -m pytest apps/presentations/tests/test_models.py --cov=presentations --cov-report=html
#
# 5. EJECUTAR EN MODO VERBOSE (más detalles):
#    python -m pytest apps/presentations/tests/test_models.py -vv
#
# 6. EJECUTAR Y PARAR EN PRIMER FALLO:
#    python -m pytest apps/presentations/tests/test_models.py -x
#
# 7. EJECUTAR TESTS QUE CONTIENEN UNA PALABRA:
#    python -m pytest apps/presentations/tests/test_models.py -k "presentation" -v
#
# 8. EJECUTAR TODOS LOS TESTS DE LA APP:
#    python -m pytest apps/presentations/tests/ -v
#
# ESTRUCTURA DE LOS TESTS:
# - TestPresentationModel: Tests para el modelo Presentation
# - TestSlideModel: Tests para el modelo Slide
# - Cada test verifica una funcionalidad específica
# - @pytest.mark.django_db permite acceso a la base de datos
#
# EJEMPLOS DE OUTPUT ESPERADO:
# ✓ 15 tests pasando
# ✓ Sin errores de importación
# ✓ Base de datos de test creada/destruida automáticamente
#
# COMANDOS ÚTILES ADICIONALES:
# - Ver qué tests existen: python -m pytest --collect-only
# - Ejecutar en paralelo: python -m pytest -n auto (requiere pytest-xdist)
# - Generar reporte HTML: python -m pytest --html=report.html
#
# ===============================================================================