# Importar Celery para que Django lo detecte
from .celery import app as celery_app

__all__ = ('celery_app',)