"""
Tareas Celery para procesamiento asíncrono de presentaciones PDF.
"""
import os
import logging
from typing import List, Optional
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from .models import Presentation, Slide

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Excepción personalizada para errores en la conversión de PDF"""
    pass


@shared_task(bind=True)
def convert_pdf_to_slides(self, presentation_id: int) -> dict:
    """
    Tarea Celery para convertir un PDF a slides individuales de manera asíncrona.

    Args:
        presentation_id: ID de la presentación a procesar

    Returns:
        dict: Resultado del procesamiento con estadísticas
    """
    try:
        # Actualizar estado: iniciando
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 0, 'status': 'Iniciando conversión PDF...'}
        )

        # Obtener la presentación
        try:
            presentation = Presentation.objects.get(id=presentation_id)
        except Presentation.DoesNotExist:
            raise PDFConversionError(f"Presentación con ID {presentation_id} no encontrada")

        if not presentation.pdf_file:
            raise PDFConversionError("La presentación no tiene archivo PDF asociado")

        logger.info(f"Iniciando conversión de PDF: {presentation.title} (ID: {presentation_id})")

        # Verificar que el archivo existe
        if not default_storage.exists(presentation.pdf_file.name):
            raise PDFConversionError(f"Archivo PDF no encontrado: {presentation.pdf_file.name}")

        # Configuración de conversión
        DPI = 200
        FORMAT = 'JPEG'
        MAX_WIDTH = 1920
        MAX_HEIGHT = 1080
        QUALITY = 85

        # Actualizar estado: convirtiendo
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 0, 'status': 'Convirtiendo PDF a imágenes...'}
        )

        # Convertir PDF a imágenes
        try:
            pdf_path = presentation.pdf_file.path
            images = convert_from_path(
                pdf_path,
                dpi=DPI,
                fmt=FORMAT.lower()
            )
        except Exception as e:
            raise PDFConversionError(f"Error al convertir PDF: {str(e)}")

        if not images:
            raise PDFConversionError("No se pudieron extraer páginas del PDF")

        total_pages = len(images)
        logger.info(f"PDF convertido: {total_pages} páginas encontradas")

        # Eliminar slides existentes
        with transaction.atomic():
            existing_slides = Slide.objects.filter(presentation=presentation)
            slides_deleted = existing_slides.count()
            existing_slides.delete()
            if slides_deleted > 0:
                logger.info(f"Eliminados {slides_deleted} slides existentes")

        slides_created = []

        # Procesar cada página como slide
        for page_num, image in enumerate(images, 1):
            try:
                # Actualizar progreso
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': page_num,
                        'total': total_pages,
                        'status': f'Procesando slide {page_num} de {total_pages}...'
                    }
                )

                # Optimizar imagen
                if image.size[0] > MAX_WIDTH or image.size[1] > MAX_HEIGHT:
                    image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

                # Convertir a RGB si es necesario
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Guardar imagen en memoria
                from io import BytesIO
                image_io = BytesIO()
                image.save(image_io, format='JPEG', quality=QUALITY, optimize=True)
                image_io.seek(0)

                # Crear nombre de archivo único
                safe_title = "".join(c for c in presentation.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title[:30]  # Limitar longitud
                filename = f"{safe_title}_slide_{page_num:03d}.jpg"

                # Crear objeto Slide
                with transaction.atomic():
                    slide = Slide.objects.create(
                        presentation=presentation,
                        slide_number=page_num
                    )

                    # Guardar imagen
                    slide.image_file.save(
                        filename,
                        ContentFile(image_io.getvalue()),
                        save=True
                    )

                slides_created.append(slide)
                logger.debug(f"Slide {page_num} creado: {filename}")

            except Exception as e:
                logger.error(f"Error creando slide {page_num}: {str(e)}")
                continue

        # Actualizar estado de la presentación a completado
        with transaction.atomic():
            presentation.processing_status = 'completed'
            presentation.is_converted = True
            presentation.total_slides = len(slides_created)
            presentation.save(update_fields=['processing_status', 'is_converted', 'total_slides'])

        # Resultado final
        result = {
            'presentation_id': presentation_id,
            'presentation_title': presentation.title,
            'slides_created': len(slides_created),
            'total_pages': total_pages,
            'status': 'completed'
        }

        logger.info(f"Conversión completada: {len(slides_created)} slides de {total_pages} páginas")
        return result

    except PDFConversionError as e:
        # Marcar presentación como fallida
        try:
            presentation = Presentation.objects.get(id=presentation_id)
            presentation.processing_status = 'failed'
            presentation.save(update_fields=['processing_status'])
            logger.error(f"Presentación marcada como fallida: {str(e)}")
        except Exception as save_error:
            logger.error(f"Error al actualizar estado fallido: {str(save_error)}")
        raise
    except Exception as e:
        # Marcar presentación como fallida
        try:
            presentation = Presentation.objects.get(id=presentation_id)
            presentation.processing_status = 'failed'
            presentation.save(update_fields=['processing_status'])
            logger.error(f"Error inesperado - presentación marcada como fallida: {str(e)}")
        except Exception as save_error:
            logger.error(f"Error al actualizar estado fallido: {str(save_error)}")
        raise PDFConversionError(f"Error inesperado: {str(e)}")