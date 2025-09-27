"""
Django settings for local development environment.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development-specific allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files for development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Development-specific logging
LOGGING['handlers']['console']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Development-specific security settings (more relaxed)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django Debug Toolbar (optional, uncomment if installed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
# INTERNAL_IPS = ['127.0.0.1']

# Development-specific cache (dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# File upload settings for development (more permissive)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# Development-specific presentations app settings
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB for development
ALLOWED_UPLOAD_EXTENSIONS = ['pdf', 'ppt', 'pptx']  # More formats for testing

