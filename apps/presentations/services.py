"""
Servicios para el procesamiento de presentaciones PDF.
"""
import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .models import Presentation, Slide

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Excepción personalizada para errores en la conversión de PDF"""
    pass


class PDFProcessor:
    """Servicio para procesar conversión de PDFs a imágenes."""

    # Configuración de conversión
    DPI = 200  # Resolución para la conversión
    FORMAT = 'PNG'  # Formato de imagen de salida
    MAX_WIDTH = 1920  # Ancho máximo de imagen
    MAX_HEIGHT = 1080  # Alto máximo de imagen
    QUALITY = 85  # Calidad de compresión

    @classmethod
    def convert_pdf_to_images(cls, presentation: Presentation) -> List[Slide]:
        """
        Convierte un PDF a imágenes individuales y crea objetos Slide.

        Args:
            presentation: Instancia de Presentation con archivo PDF

        Returns:
            Lista de objetos Slide creados

        Raises:
            PDFConversionError: Error durante la conversión
        """
        if not presentation.pdf_file:
            raise PDFConversionError("La presentación no tiene archivo PDF asociado")

        logger.info(f"Iniciando conversión de PDF para presentación {presentation.id}")

        try:
            # Obtener ruta absoluta del PDF
            pdf_path = presentation.pdf_file.path

            # Verificar que el archivo existe
            if not os.path.exists(pdf_path):
                raise PDFConversionError(f"Archivo PDF no encontrado: {pdf_path}")

            # Convertir PDF a imágenes
            images = cls._convert_pdf_pages(pdf_path)

            # Crear slides en la base de datos
            slides = cls._create_slides_from_images(presentation, images)

            # Actualizar estado de la presentación
            presentation.total_slides = len(slides)
            presentation.is_converted = True
            presentation.save()

            logger.info(f"Conversión completada: {len(slides)} slides creados")
            return slides

        except Exception as e:
            logger.error(f"Error en conversión de PDF {presentation.id}: {str(e)}")
            raise PDFConversionError(f"Error al convertir PDF: {str(e)}")

    @classmethod
    def _convert_pdf_pages(cls, pdf_path: str) -> List[Image.Image]:
        """
        Convierte páginas de PDF a objetos Image de PIL.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Lista de objetos Image
        """
        try:
            # Convertir PDF a imágenes usando pdf2image
            images = convert_from_path(
                pdf_path,
                dpi=cls.DPI,
                output_folder=None,  # Mantener en memoria
                first_page=None,
                last_page=None,
                fmt=cls.FORMAT.lower(),
                thread_count=1,  # Para mayor estabilidad
                userpw=None,
                use_cropbox=False,
                strict=False
            )

            # Optimizar tamaño de imágenes
            optimized_images = []
            for img in images:
                optimized_img = cls._optimize_image(img)
                optimized_images.append(optimized_img)

            return optimized_images

        except Exception as e:
            raise PDFConversionError(f"Error al procesar páginas PDF: {str(e)}")

    @classmethod
    def _optimize_image(cls, image: Image.Image) -> Image.Image:
        """
        Optimiza una imagen redimensionando si es necesario.

        Args:
            image: Imagen PIL a optimizar

        Returns:
            Imagen optimizada
        """
        # Obtener dimensiones actuales
        width, height = image.size

        # Calcular nuevo tamaño manteniendo proporción
        if width > cls.MAX_WIDTH or height > cls.MAX_HEIGHT:
            # Calcular ratio de reducción
            width_ratio = cls.MAX_WIDTH / width
            height_ratio = cls.MAX_HEIGHT / height
            ratio = min(width_ratio, height_ratio)

            # Calcular nuevas dimensiones
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # Redimensionar imagen
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    @classmethod
    def _create_slides_from_images(cls, presentation: Presentation, images: List[Image.Image]) -> List[Slide]:
        """
        Crea objetos Slide a partir de imágenes.

        Args:
            presentation: Presentación a la que pertenecen los slides
            images: Lista de imágenes PIL

        Returns:
            Lista de slides creados
        """
        slides = []

        # Eliminar slides existentes si los hay
        presentation.slides.all().delete()

        for i, image in enumerate(images, 1):
            try:
                # Crear nombre único para el archivo
                filename = f"presentation_{presentation.id}_slide_{i}.{cls.FORMAT.lower()}"

                # Convertir imagen PIL a bytes
                image_bytes = cls._image_to_bytes(image)

                # Crear archivo Django
                image_file = ContentFile(image_bytes, name=filename)

                # Crear objeto Slide
                slide = Slide.objects.create(
                    presentation=presentation,
                    slide_number=i,
                    image_file=image_file
                )

                slides.append(slide)
                logger.debug(f"Slide {i} creado: {slide.image_file.name}")

            except Exception as e:
                logger.error(f"Error creando slide {i}: {str(e)}")
                # Continuar con el siguiente slide
                continue

        return slides

    @classmethod
    def _image_to_bytes(cls, image: Image.Image) -> bytes:
        """
        Convierte imagen PIL a bytes.

        Args:
            image: Imagen PIL

        Returns:
            Bytes de la imagen
        """
        from io import BytesIO

        # Convertir a RGB si es necesario (para PNG)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Guardar en BytesIO
        buffer = BytesIO()

        # Configurar opciones según formato
        save_kwargs = {}
        if cls.FORMAT.upper() == 'JPEG':
            save_kwargs['quality'] = cls.QUALITY
            save_kwargs['optimize'] = True

        image.save(buffer, format=cls.FORMAT, **save_kwargs)
        return buffer.getvalue()

    @classmethod
    def get_conversion_status(cls, presentation: Presentation) -> dict:
        """
        Obtiene información sobre el estado de conversión.

        Args:
            presentation: Presentación a verificar

        Returns:
            Diccionario con información de estado
        """
        return {
            'is_converted': presentation.is_converted,
            'total_slides': presentation.total_slides,
            'slides_count': presentation.slides.count(),
            'has_pdf': bool(presentation.pdf_file),
            'pdf_filename': presentation.get_filename(),
            'pdf_size_mb': presentation.file_size_mb
        }