# config/settings/production.py
import os
import json
from .base import * # Importa todas las configuraciones base

# === Production Specific Settings ===
# Estas variables DEBEN estar definidas en el entorno del servidor de producción

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY_PROD')
if not SECRET_KEY:
    raise ValueError("CRITICAL: DJANGO_SECRET_KEY_PROD no está configurada para producción!")

DEBUG = False # Siempre False en producción

ALLOWED_HOSTS_PROD = os.environ.get('DJANGO_ALLOWED_HOSTS_PROD')
if not ALLOWED_HOSTS_PROD:
    raise ValueError("CRITICAL: DJANGO_ALLOWED_HOSTS_PROD no está configurada.")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_PROD.split(',') if host.strip()]

# --- Database Configuration for Production (ej. SQL Server) ---
db_options_json_prod = os.environ.get('DB_OPTIONS_PROD_JSON', '{}')
try:
    db_options_prod = json.loads(db_options_json_prod) # Asegúrate que este JSON sea seguro para prod
except json.JSONDecodeError:
    print(f"ADVERTENCIA (settings): DB_OPTIONS_PROD_JSON no es un JSON válido. Usando opciones por defecto.")
    db_options_prod = {"driver": "ODBC Driver 18 for SQL Server", "Encrypt": "yes", "TrustServerCertificate": "no"} # Ejemplo, no confiar ciegamente

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE_PROD', 'mssql'),
        'NAME': os.environ.get('DB_NAME_PROD'),
        'USER': os.environ.get('DB_USER_PROD'),
        'PASSWORD': os.environ.get('DB_PASSWORD_PROD'),
        'HOST': os.environ.get('DB_HOST_PROD'),
        'PORT': os.environ.get('DB_PORT_PROD', ''),
        'OPTIONS': db_options_prod,
    }
}
# Validar que las variables de DB de producción estén configuradas
for key in ['DB_NAME_PROD', 'DB_USER_PROD', 'DB_PASSWORD_PROD', 'DB_HOST_PROD']:
    if not os.environ.get(key):
        raise ValueError(f"CRITICAL: La variable de entorno de base de datos '{key}' no está configurada para producción.")


# Media files for Production (Azure, S3, etc.)
# DEFAULT_FILE_STORAGE = os.environ.get('DJANGO_DEFAULT_FILE_STORAGE_PROD', 'storages.backends.azure_storage.AzureStorage')
# AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME_PROD')
# AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY_PROD')
# AZURE_MEDIA_CONTAINER = os.environ.get('AZURE_MEDIA_CONTAINER_PROD', 'media')
# MEDIA_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_MEDIA_CONTAINER}/'
# MEDIA_ROOT no es necesario si usas storage en la nube para media.

# Static files for Production (Whitenoise o S3/Azure)
STATIC_ROOT = BASE_DIR / 'staticfiles_collected' # Directorio donde collectstatic reunirá los archivos
# STATICFILES_STORAGE = os.environ.get('DJANGO_STATICFILES_STORAGE_PROD', 'whitenoise.storage.CompressedManifestStaticFilesStorage')
# O si usas Azure/S3 para estáticos:
# AZURE_STATIC_CONTAINER = os.environ.get('AZURE_STATIC_CONTAINER_PROD', 'static')
# STATIC_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_STATIC_CONTAINER}/'

# CORS for Production
CORS_ALLOWED_ORIGINS_PROD = os.environ.get('CORS_ALLOWED_ORIGINS_PROD') # Ej: 'https://app.dloub.com,https://kukenan.dloub.com'
if not CORS_ALLOWED_ORIGINS_PROD:
    print("ADVERTENCIA (settings): CORS_ALLOWED_ORIGINS_PROD no está configurada. CORS podría no funcionar.")
    CORS_ALLOWED_ORIGINS = []
else:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_PROD.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS_PROD', 'True').lower() in ('true', '1', 't') # O False si no se necesitan cookies cross-origin

# Django REST Framework - Production specific (sin Browsable API)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ('rest_framework.renderers.JSONRenderer',)

# Simple JWT - Production specific
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY # Usar la SECRET_KEY de producción

# Logging - Production specific (menos verboso, errores a mail_admins o sistema de logging externo)
LOGGING['loggers']['django.db.backends']['level'] = 'INFO' # No mostrar queries SQL en prod por defecto
LOGGING['loggers']['src']['level'] = 'INFO'
# Configurar handlers para 'mail_admins' o integración con Sentry/Datadog etc.
# LOGGING['handlers']['mail_admins'] = { ... }
# LOGGING['loggers']['django.request']['handlers'] = ['mail_admins', 'console'] # Enviar errores de request a admins

# Email - Production (usar un servicio real como SendGrid, SES, etc.)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST_PROD')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT_PROD', 587))
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER_PROD')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD_PROD')
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL_PROD', 'noreply@dloubplatform.com')

# HTTPS Settings (asegurados por el proxy inverso como Nginx o el balanceador de carga)
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# --- MENSAJES DE ARRANQUE PARA PRODUCCIÓN ---
# Es menos común imprimir tanto en producción, pero útil para verificar la carga.
# print("=" * 50)
# print("🚀 DLOUB+ PLATFORM - PRODUCTION SETTINGS LOADED 🚀")
# ... (prints relevantes para producción) ...
# print("=" * 50)