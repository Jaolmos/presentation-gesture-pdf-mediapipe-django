"""
Tests para formularios de la aplicación presentations.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.presentations.forms import PresentationUploadForm


@pytest.mark.django_db
class TestPresentationUploadForm:
    """Tests para el formulario PresentationUploadForm."""

    def test_form_valid_data(self):
        """Test que verifica que el formulario es válido con datos correctos."""
        # Simular archivo PDF válido
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': 'Mi Presentación de Prueba'
        }
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert form.is_valid(), f"Form should be valid, errors: {form.errors}"

    def test_form_missing_title(self):
        """Test que verifica que el formulario es inválido sin título."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {}  # Sin título
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_form_empty_title(self):
        """Test que verifica que el formulario es inválido con título vacío."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': ''  # Título vacío
        }
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_form_title_too_short(self):
        """Test que verifica que el formulario es inválido con título muy corto."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': 'AB'  # Solo 2 caracteres
        }
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_form_missing_pdf_file(self):
        """Test que verifica que el formulario es inválido sin archivo PDF."""
        form_data = {
            'title': 'Mi Presentación de Prueba'
        }
        file_data = {}  # Sin archivo

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'pdf_file' in form.errors

    def test_form_invalid_file_type(self):
        """Test que verifica que el formulario es inválido con archivo no-PDF."""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is not a PDF file",
            content_type="text/plain"
        )

        form_data = {
            'title': 'Mi Presentación de Prueba'
        }
        file_data = {
            'pdf_file': txt_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'pdf_file' in form.errors

    def test_form_wrong_file_extension(self):
        """Test que verifica validación de extensión de archivo."""
        # Archivo con contenido PDF pero extensión incorrecta
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        wrong_file = SimpleUploadedFile(
            "test.doc",  # Extensión incorrecta
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': 'Mi Presentación de Prueba'
        }
        file_data = {
            'pdf_file': wrong_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'pdf_file' in form.errors

    def test_form_file_too_large(self):
        """Test que verifica validación de tamaño máximo de archivo."""
        # Crear archivo simulando más de 50MB
        large_content = b'%PDF-1.4\n' + b'x' * (51 * 1024 * 1024)  # ~51MB
        large_file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': 'Mi Presentación de Prueba'
        }
        file_data = {
            'pdf_file': large_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'pdf_file' in form.errors

    def test_form_title_max_length(self):
        """Test que verifica longitud máxima del título."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        # Título de exactamente 200 caracteres (límite)
        long_title = 'A' * 200
        form_data = {
            'title': long_title
        }
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert form.is_valid(), f"Form should be valid with 200 char title, errors: {form.errors}"

        # Título de 201 caracteres (excede límite)
        too_long_title = 'A' * 201
        form_data = {
            'title': too_long_title
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_form_clean_title_strips_whitespace(self):
        """Test que verifica que el título se limpia de espacios en blanco."""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        form_data = {
            'title': '   Mi Presentación   '  # Con espacios
        }
        file_data = {
            'pdf_file': pdf_file
        }

        form = PresentationUploadForm(data=form_data, files=file_data)
        assert form.is_valid()
        assert form.cleaned_data['title'] == 'Mi Presentación'