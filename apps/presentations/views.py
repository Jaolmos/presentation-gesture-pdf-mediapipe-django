from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    """Vista principal de la aplicación SlideMotion"""
    return HttpResponse("¡Bienvenido a SlideMotion! - Configuración inicial completada")
