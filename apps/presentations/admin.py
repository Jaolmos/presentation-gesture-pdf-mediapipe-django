from django.contrib import admin
from django.utils.html import format_html
from .models import Presentation, Slide


class SlideInline(admin.TabularInline):
    """Inline para mostrar slides dentro de la presentación"""
    model = Slide
    extra = 0
    readonly_fields = ['image_preview', 'image_size_mb', 'created_at']
    fields = ['slide_number', 'image_file', 'image_preview', 'image_size_mb', 'created_at']

    def image_preview(self, obj):
        """Mostrar preview pequeño de la imagen del slide"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image_file.url
            )
        return "Sin imagen"
    image_preview.short_description = "Preview"


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    """Admin personalizado para Presentation"""

    list_display = [
        'title',
        'total_slides',
        'is_converted',
        'file_size_mb',
        'created_at'
    ]

    list_filter = [
        'is_converted',
        'created_at',
    ]

    search_fields = [
        'title',
    ]

    readonly_fields = [
        'total_slides',
        'is_converted',
        'file_size_mb',
        'get_filename',
        'created_at',
        'updated_at'
    ]

    fields = [
        'title',
        'pdf_file',
        'get_filename',
        'file_size_mb',
        'total_slides',
        'is_converted',
        'created_at',
        'updated_at',
    ]

    inlines = [SlideInline]

    def get_filename(self, obj):
        """Mostrar solo el nombre del archivo"""
        return obj.get_filename() or "Sin archivo"
    get_filename.short_description = "Nombre del archivo"


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    """Admin personalizado para Slide"""

    list_display = [
        'presentation',
        'slide_number',
        'image_preview',
        'image_size_mb',
        'created_at'
    ]

    list_filter = [
        'presentation',
        'created_at',
    ]

    search_fields = [
        'presentation__title',
    ]

    readonly_fields = [
        'image_preview',
        'image_size_mb',
        'created_at'
    ]

    fields = [
        'presentation',
        'slide_number',
        'image_file',
        'image_preview',
        'image_size_mb',
        'created_at',
    ]

    def image_preview(self, obj):
        """Mostrar preview de la imagen del slide"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px;" />',
                obj.image_file.url
            )
        return "Sin imagen"
    image_preview.short_description = "Preview del slide"
