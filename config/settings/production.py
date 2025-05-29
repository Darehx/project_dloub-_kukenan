# config/settings/production.py
from .base import * # Importa todo de base.py
import os

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("CRITICAL: DJANGO_SECRET_KEY no está configurada para producción.")

DEBUG = False # Siempre False en producción

ALLOWED_HOSTS_CSV = os.environ.get('DJANGO_ALLOWED_HOSTS')
if not ALLOWED_HOSTS_CSV:
    raise ValueError("CRITICAL: DJANGO_ALLOWED_HOSTS no está configurado para producción.")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_CSV.split(',') if host.strip()]

# Configuración de Base de Datos para Producción (leída de .env)
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE'), # Ej: 'mssql', 'django_pyodbc_azure', 'django.db.backends.postgresql'
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', ''), # Vacío para default del driver
        'OPTIONS': {
            # 'driver': os.environ.get('DB_OPTIONS_DRIVER'), # Ejemplo
            # ... otras opciones de producción, timeouts, SSL, etc.
        },
    }
}
if not all([DATABASES['default'].get(k) for k in ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST']]):
    raise ValueError("CRITICAL: La configuración de la base de datos de producción está incompleta.")

# CORS para Producción
CORS_ALLOWED_ORIGINS_CSV = os.environ.get('CORS_ALLOWED_ORIGINS')
if CORS_ALLOWED_ORIGINS_CSV:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_CSV.split(',') if origin.strip()]
else:
    # Decide una política por defecto: o fallar o no permitir ninguno si no está explícito.
    # CORS_ALLOWED_ORIGINS = []
    raise ValueError("CRITICAL: CORS_ALLOWED_ORIGINS no está configurado para producción.")

# CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', 'True') == 'True' # Si es necesario

# Static & Media files para Producción (ej. S3, Azure Blob)
# STATIC_ROOT = BASE_DIR / "staticfiles" # Donde collectstatic pondrá los archivos
# MEDIA_ROOT = BASE_DIR / "mediafiles"   # Donde se guardarán los archivos subidos por defecto si no usas storage externo
# DEFAULT_FILE_STORAGE = os.environ.get('DJANGO_DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
# STATICFILES_STORAGE = os.environ.get('DJANGO_STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')

# if DEFAULT_FILE_STORAGE == 'storages.backends.azure_storage.AzureStorage':
#     AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
#     AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
#     AZURE_MEDIA_CONTAINER = os.environ.get('AZURE_MEDIA_CONTAINER')
#     if not all([AZURE_ACCOUNT_NAME, AZURE_ACCOUNT_KEY, AZURE_MEDIA_CONTAINER]):
#         raise ValueError("CRITICAL: Configuración de Azure Storage incompleta.")

# Email para Producción
# EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
# EMAIL_HOST = os.environ.get('EMAIL_HOST')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
# if not all([EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]):
#    print("ADVERTENCIA: Configuración de Email para producción incompleta. Los correos podrían no enviarse.")


# Logging para Producción (puede ser más restrictivo o enviar a servicios externos)
LOGGING['root']['level'] = os.environ.get('DJANGO_ROOT_LOG_LEVEL_PROD', 'INFO')
LOGGING['loggers']['django']['level'] = os.environ.get('DJANGO_LOG_LEVEL_PROD', 'INFO')
LOGGING['loggers']['src']['level'] = os.environ.get('SRC_LOG_LEVEL_PROD', 'INFO')
# Añadir 'file' handler para producción si es necesario:
# LOGGING['handlers']['file'] = {
#     'level': 'INFO',
#     'class': 'logging.handlers.RotatingFileHandler', # o FileHandler
#     'filename': BASE_DIR / 'logs/django_production.log',
#     'maxBytes': 1024*1024*5, # 5 MB
#     'backupCount': 5,
#     'formatter': 'verbose',
# }
# LOGGING['root']['handlers'] = ['console', 'file'] # Añadir 'file'

# Consideraciones de Seguridad para Producción:
# SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'
# SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'True') == 'True'
# CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'True') == 'True'
# SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', 31536000)) # 1 año
# SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
# SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'True') == 'True'
# SECURE_BROWSER_XSS_FILTER = True
# X_FRAME_OPTIONS = 'DENY'