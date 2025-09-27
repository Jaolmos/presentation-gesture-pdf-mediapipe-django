import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Seleccionar configuración según ENVIRONMENT
environment = os.getenv('ENVIRONMENT', 'local')

if environment == 'production':
    from .production import *
else:
    from .local import *