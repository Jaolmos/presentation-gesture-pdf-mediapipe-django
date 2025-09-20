from django import forms
from django.core.exceptions import ValidationError
from .models import Presentation


class PresentationUploadForm(forms.ModelForm):
    """Formulario para cargar presentaciones PDF"""

    class Meta:
        model = Presentation
        fields = ['title', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la presentación',
                'required': True,
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
                'required': True,
            }),
        }
        labels = {
            'title': 'Título de la presentación',
            'pdf_file': 'Archivo PDF',
        }
        help_texts = {
            'title': 'Nombre descriptivo para identificar tu presentación',
            'pdf_file': 'Selecciona un archivo PDF (máximo 50MB)',
        }

    def clean_pdf_file(self):
        """Validación personalizada para el archivo PDF"""
        pdf_file = self.cleaned_data.get('pdf_file')

        if pdf_file:
            # Validar tamaño del archivo (50MB máximo)
            max_size = 50 * 1024 * 1024  # 50MB en bytes
            if pdf_file.size > max_size:
                raise ValidationError(
                    f'El archivo es demasiado grande. Tamaño máximo: 50MB. '
                    f'Tu archivo: {pdf_file.size / (1024 * 1024):.1f}MB'
                )

            # Validar extensión del archivo
            if not pdf_file.name.lower().endswith('.pdf'):
                raise ValidationError(
                    'Solo se permiten archivos PDF. '
                    f'Tu archivo: {pdf_file.name}'
                )

            # Validar content type
            allowed_content_types = ['application/pdf']
            if hasattr(pdf_file, 'content_type') and pdf_file.content_type not in allowed_content_types:
                raise ValidationError(
                    'Tipo de archivo no válido. Solo se permiten archivos PDF.'
                )

        return pdf_file

    def clean_title(self):
        """Validación personalizada para el título"""
        title = self.cleaned_data.get('title')

        if title:
            # Limpiar espacios extra
            title = title.strip()

            # Validar longitud mínima
            if len(title) < 3:
                raise ValidationError(
                    'El título debe tener al menos 3 caracteres.'
                )

            # Validar que no sea solo espacios
            if not title:
                raise ValidationError(
                    'El título no puede estar vacío.'
                )

        return title

    def save(self, commit=True):
        """Guardar presentación con procesamiento adicional"""
        presentation = super().save(commit=False)

        # Limpiar título
        presentation.title = presentation.title.strip()

        if commit:
            presentation.save()

        return presentation