from django.db import models
from django.core.validators import FileExtensionValidator
from pathlib import Path


class Presentation(models.Model):
    """Modelo para almacenar información de presentaciones PDF"""

    title = models.CharField(
        max_length=200,
        help_text="Título de la presentación"
    )

    pdf_file = models.FileField(
        upload_to='presentations/pdfs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Archivo PDF de la presentación"
    )

    total_slides = models.PositiveIntegerField(
        default=0,
        help_text="Número total de slides en la presentación"
    )

    is_converted = models.BooleanField(
        default=False,
        help_text="Indica si el PDF ya fue convertido a imágenes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de última actualización"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Presentación"
        verbose_name_plural = "Presentaciones"

    def __str__(self):
        return self.title

    @property
    def file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        if self.pdf_file:
            return round(self.pdf_file.size / (1024 * 1024), 2)
        return 0

    def get_filename(self):
        """Retorna solo el nombre del archivo sin la ruta"""
        if self.pdf_file:
            return Path(self.pdf_file.name).name
        return ""


class Slide(models.Model):
    """Modelo para slides individuales de una presentación"""

    presentation = models.ForeignKey(
        Presentation,
        on_delete=models.CASCADE,
        related_name='slides',
        help_text="Presentación a la que pertenece este slide"
    )

    slide_number = models.PositiveIntegerField(
        help_text="Número del slide dentro de la presentación"
    )

    image_file = models.ImageField(
        upload_to='presentations/slides/',
        help_text="Imagen del slide convertida desde PDF"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación"
    )

    class Meta:
        ordering = ['presentation', 'slide_number']
        unique_together = ['presentation', 'slide_number']
        verbose_name = "Slide"
        verbose_name_plural = "Slides"

    def __str__(self):
        return f"{self.presentation.title} - Slide {self.slide_number}"

    @property
    def image_size_mb(self):
        """Retorna el tamaño de la imagen en MB"""
        if self.image_file:
            return round(self.image_file.size / (1024 * 1024), 2)
        return 0
