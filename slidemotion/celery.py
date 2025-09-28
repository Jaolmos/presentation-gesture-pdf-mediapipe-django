"""
Configuración de Celery para SlideMotion
"""

import os
from celery import Celery

# Establecer el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slidemotion.settings')

app = Celery('slidemotion')

# Usar configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrimiento de tareas en todas las apps instaladas
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para probar que Celery funciona"""
    print(f'Request: {self.request!r}')