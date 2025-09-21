from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from .models import Presentation
from .forms import PresentationUploadForm
from .services import PDFProcessor, PDFConversionError


def home(request):
    """Vista principal - Lista de presentaciones y formulario de carga"""
    presentations = Presentation.objects.all()

    # Paginación (10 presentaciones por página)
    paginator = Paginator(presentations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'presentations': page_obj,
        'total_presentations': presentations.count(),
    }

    return render(request, 'presentations/home.html', context)


def home_content(request):
    """Vista para cargar contenido de la página de inicio dinámicamente"""
    presentations = Presentation.objects.all()

    # Paginación (10 presentaciones por página)
    paginator = Paginator(presentations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'presentations': page_obj,
        'total_presentations': presentations.count(),
    }

    return render(request, 'presentations/home_content.html', context)


def upload_presentation(request):
    """Vista para cargar nuevas presentaciones"""
    if request.method == 'POST':
        form = PresentationUploadForm(request.POST, request.FILES)

        if form.is_valid():
            presentation = form.save()

            # Intentar conversión inmediata del PDF
            try:
                slides = PDFProcessor.convert_pdf_to_images(presentation)
                messages.success(
                    request,
                    f'Presentación "{presentation.title}" cargada y convertida exitosamente. '
                    f'{len(slides)} slides creados.'
                )
            except PDFConversionError as e:
                messages.warning(
                    request,
                    f'Presentación "{presentation.title}" cargada, pero hubo un error en la conversión: {str(e)}'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Presentación "{presentation.title}" cargada, pero hubo un error inesperado: {str(e)}'
                )

            return redirect('presentations:presentation_detail', pk=presentation.pk)

        else:
            messages.error(
                request,
                'Error al cargar la presentación. Revisa los campos marcados.'
            )

    else:
        form = PresentationUploadForm()

    context = {
        'form': form,
        'title': 'Subir nueva presentación'
    }

    return render(request, 'presentations/upload.html', context)


def upload_presentation_htmx(request):
    """Vista HTMX para cargar presentaciones de forma asíncrona"""
    if request.method == 'POST':
        form = PresentationUploadForm(request.POST, request.FILES)

        if form.is_valid():
            presentation = form.save()

            # Intentar conversión inmediata del PDF
            conversion_message = ""
            conversion_status = "success"

            try:
                slides = PDFProcessor.convert_pdf_to_images(presentation)
                conversion_message = f'Presentación "{presentation.title}" cargada y convertida exitosamente. {len(slides)} slides creados.'
            except PDFConversionError as e:
                conversion_message = f'Presentación "{presentation.title}" cargada, pero hubo un error en la conversión: {str(e)}'
                conversion_status = "warning"
            except Exception as e:
                conversion_message = f'Presentación "{presentation.title}" cargada, pero hubo un error inesperado: {str(e)}'
                conversion_status = "warning"

            context = {
                'success': True,
                'presentation': presentation,
                'message': conversion_message,
                'status': conversion_status
            }
            return render(request, 'presentations/upload_result.html', context)

        else:
            # Devolver formulario con errores
            context = {
                'form': form,
                'success': False
            }
            return render(request, 'presentations/upload_form.html', context)

    # GET request - devolver formulario limpio
    form = PresentationUploadForm()
    context = {
        'form': form,
        'success': None
    }
    return render(request, 'presentations/upload_form.html', context)


def presentation_detail(request, pk):
    """Vista de detalle de una presentación"""
    presentation = get_object_or_404(Presentation, pk=pk)

    context = {
        'presentation': presentation,
        'slides': presentation.slides.all() if presentation.is_converted else None,
    }

    return render(request, 'presentations/detail.html', context)


def presentation_list(request):
    """Vista de lista de presentaciones (alternativa a home)"""
    presentations = Presentation.objects.all()

    # Filtros opcionales
    search_query = request.GET.get('search', '')
    if search_query:
        presentations = presentations.filter(title__icontains=search_query)

    converted_filter = request.GET.get('converted', '')
    if converted_filter == 'yes':
        presentations = presentations.filter(is_converted=True)
    elif converted_filter == 'no':
        presentations = presentations.filter(is_converted=False)

    # Paginación
    paginator = Paginator(presentations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'presentations': page_obj,
        'search_query': search_query,
        'converted_filter': converted_filter,
        'title': 'Todas las presentaciones',
    }

    return render(request, 'presentations/list.html', context)


def presentation_list_content(request):
    """Vista para cargar contenido de lista de presentaciones dinámicamente"""
    presentations = Presentation.objects.all()

    # Filtros opcionales
    search_query = request.GET.get('search', '')
    if search_query:
        presentations = presentations.filter(title__icontains=search_query)

    converted_filter = request.GET.get('converted', '')
    if converted_filter == 'yes':
        presentations = presentations.filter(is_converted=True)
    elif converted_filter == 'no':
        presentations = presentations.filter(is_converted=False)

    # Paginación
    paginator = Paginator(presentations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'presentations': page_obj,
        'search_query': search_query,
        'converted_filter': converted_filter,
    }

    return render(request, 'presentations/list_content.html', context)


def delete_presentation(request, pk):
    """Vista para eliminar una presentación con confirmación"""
    presentation = get_object_or_404(Presentation, pk=pk)

    if request.method == 'POST':
        # Confirmar eliminación
        presentation_title = presentation.title
        try:
            presentation.delete()
            messages.success(
                request,
                f'Presentación "{presentation_title}" eliminada exitosamente.'
            )
            return redirect('presentations:home')
        except Exception as e:
            messages.error(
                request,
                f'Error al eliminar la presentación: {str(e)}'
            )
            return redirect('presentations:presentation_detail', pk=pk)

    context = {
        'presentation': presentation,
        'title': f'Eliminar "{presentation.title}"'
    }

    return render(request, 'presentations/delete_confirm.html', context)


def delete_presentation_htmx(request, pk):
    """Vista HTMX para eliminar presentación de forma asíncrona"""
    presentation = get_object_or_404(Presentation, pk=pk)

    if request.method == 'POST':
        # Confirmar eliminación
        presentation_title = presentation.title
        try:
            presentation.delete()
            context = {
                'success': True,
                'message': f'Presentación "{presentation_title}" eliminada exitosamente.'
            }
            return render(request, 'presentations/delete_result.html', context)
        except Exception as e:
            context = {
                'success': False,
                'message': f'Error al eliminar la presentación: {str(e)}',
                'presentation': presentation
            }
            return render(request, 'presentations/delete_confirm_content.html', context)

    # GET request - mostrar confirmación
    context = {
        'presentation': presentation,
    }
    return render(request, 'presentations/delete_confirm_content.html', context)


def camera_config(request):
    """Vista de configuración de cámara y gestos"""
    context = {
        'title': 'Configuración de Cámara y Gestos'
    }

    return render(request, 'presentations/camera_config.html', context)


def presentation_mode(request, pk):
    """Vista principal del modo presentación fullscreen"""
    presentation = get_object_or_404(Presentation, pk=pk)

    # Verificar que la presentación esté convertida
    if not presentation.is_converted:
        messages.error(request, 'La presentación no ha sido convertida aún.')
        return redirect('presentations:presentation_detail', pk=pk)

    # Obtener todos los slides ordenados
    slides = presentation.slides.all().order_by('slide_number')

    if not slides.exists():
        messages.error(request, 'Esta presentación no tiene slides disponibles.')
        return redirect('presentations:presentation_detail', pk=pk)

    context = {
        'presentation': presentation,
        'total_slides': slides.count(),
        'current_slide': slides.first(),
        'current_slide_number': 1,
        'title': f'Presentación: {presentation.title}'
    }

    return render(request, 'presentations/presentation_mode.html', context)


def presentation_slide(request, pk, slide_number):
    """Vista AJAX para cambiar de slide en modo presentación"""
    presentation = get_object_or_404(Presentation, pk=pk)

    # Obtener todos los slides ordenados
    slides = presentation.slides.all().order_by('slide_number')
    total_slides = slides.count()

    # Validar número de slide
    if slide_number < 1 or slide_number > total_slides:
        return JsonResponse({
            'error': 'Número de slide inválido',
            'current_slide': 1,
            'total_slides': total_slides
        }, status=400)

    # Obtener el slide específico
    try:
        current_slide = slides[slide_number - 1]
    except IndexError:
        return JsonResponse({
            'error': 'Slide no encontrado',
            'current_slide': 1,
            'total_slides': total_slides
        }, status=404)

    # Devolver datos del slide para navegación AJAX
    return JsonResponse({
        'slide_image_url': current_slide.image_file.url,
        'slide_number': slide_number,
        'total_slides': total_slides,
        'presentation_title': presentation.title,
        'has_previous': slide_number > 1,
        'has_next': slide_number < total_slides
    })
