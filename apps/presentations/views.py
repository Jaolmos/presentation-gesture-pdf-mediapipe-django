from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
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
