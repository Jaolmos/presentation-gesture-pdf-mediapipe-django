import os
import django
from django.conf import settings

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slidemotion.settings')
django.setup()