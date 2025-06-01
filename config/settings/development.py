# config/settings/development.py
import os
import json
from .base import * # Importa todas las configuraciones base

# === Development Specific Settings ===

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY_DEV', 'unsafe-dev-dloub-secret-key_CHANGE_ME_$(*@#!)')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS_DEV = os.environ.get('DJANGO_ALLOWED_HOSTS_DEV', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_DEV.split(',') if host.strip()]

# --- Database Configuration for Development ---
DB_ENGINE_CHOICE = os.environ.get('DB_ENGINE_CHOICE_DEV', 'sqlite').lower()

if DB_ENGINE_CHOICE == 'sqlite':
    SQLITE_DB_NAME = os.environ.get('DB_SQLITE_NAME_DEV', 'dloub_platform_dev.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / SQLITE_DB_NAME,
        }
    }
    print(f"INFO (settings): Using SQLite database: {DATABASES['default']['NAME']}")
elif DB_ENGINE_CHOICE == 'mssql':
    db_options_json = os.environ.get('DB_OPTIONS_MSSQL_DEV_JSON', '{}')
    try:
        db_options = json.loads(db_options_json)
    except json.JSONDecodeError:
        print(f"ADVERTENCIA (settings): DB_OPTIONS_MSSQL_DEV_JSON no es un JSON válido. Usando opciones por defecto. Valor: {db_options_json}")
        db_options = {} # O un default seguro para desarrollo

    DATABASES = {
        'default': {
            'ENGINE': 'mssql', # El .env no necesita DB_ENGINE_MSSQL_DEV
            'NAME': os.environ.get('DB_NAME_MSSQL_DEV'),
            'USER': os.environ.get('DB_USER_MSSQL_DEV', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD_MSSQL_DEV', ''),
            'HOST': os.environ.get('DB_HOST_MSSQL_DEV'),
            'PORT': os.environ.get('DB_PORT_MSSQL_DEV', ''), # Puerto puede ser string vacío
            'OPTIONS': db_options,
        }
    }
    # Validar que las variables de MSSQL Dev estén presentes si se elige mssql
    if not DATABASES['default']['NAME'] or not DATABASES['default']['HOST']:
        raise ValueError("Para DB_ENGINE_CHOICE_DEV='mssql', DB_NAME_MSSQL_DEV y DB_HOST_MSSQL_DEV deben estar definidos en .env")
    print(f"INFO (settings): Using MSSQL database: {DATABASES['default']['NAME']} on {DATABASES['default']['HOST']}")
else:
    raise ValueError(f"DB_ENGINE_CHOICE_DEV no reconocido: '{DB_ENGINE_CHOICE}'. Opciones: 'sqlite', 'mssql'.")


# Media files for Development (local storage)
MEDIA_ROOT_DEV_FOLDER = os.environ.get('DJANGO_MEDIA_ROOT_DEV', 'mediafiles_dev_local')
MEDIA_ROOT = BASE_DIR / MEDIA_ROOT_DEV_FOLDER
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Static files (Development - Django sirve los estáticos)
#STATICFILES_DIRS = [
#    BASE_DIR / "static_global", # Si tienes una carpeta global de estáticos
#]
# No necesitas STATIC_ROOT en desarrollo si DEBUG=True y usas el servidor de desarrollo de Django

# CORS for Development
CORS_ALLOWED_ORIGINS_DEV = os.environ.get('CORS_ALLOWED_ORIGINS_DEV', 'http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_DEV.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS_DEV', 'True').lower() in ('true', '1', 't')
# CORS_ALLOW_ALL_ORIGINS = True # Descomenta si necesitas permitir todos para dev simple, pero es menos seguro

# Django REST Framework - Development specific
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer', # Habilitar Browsable API en desarrollo
)

# Simple JWT - Development specific
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY # Usar la SECRET_KEY de desarrollo

# Logging - Development specific (más verboso)
SQL_DEBUG = os.environ.get('SQL_DEBUG', 'True').lower() in ('true', '1', 't')
if SQL_DEBUG:
    LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'
LOGGING['loggers']['src']['level'] = os.environ.get('SRC_LOG_LEVEL', 'DEBUG') # Más verboso para tus apps

# Email - Development (consola o Mailhog/Mailtrap)
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.console.EmailBackend' # Default a consola
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND_DEV', EMAIL_BACKEND_DEFAULT)
if EMAIL_BACKEND != EMAIL_BACKEND_DEFAULT: # Si se define algo diferente en .env
    EMAIL_HOST = os.environ.get('EMAIL_HOST_DEV')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT_DEV', 25))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER_DEV')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD_DEV')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS_DEV', 'True').lower() in ('true', '1', 't') # Ajusta según tu proveedor
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL_DEV', 'dev-noreply@dloubplatform.com')

# Django Debug Toolbar (si la instalas)
# INSTALLED_APPS.append('debug_toolbar')
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware') # O en una posición adecuada
# INTERNAL_IPS = [host.strip() for host in os.environ.get('INTERNAL_IPS_DEV', '127.0.0.1').split(',') if host.strip()]

# --- MENSAJES DE ARRANQUE PARA DESARROLLO ---
print("=" * 50)
print("🚀 DLOUB+ PLATFORM - DEVELOPMENT SETTINGS LOADED 🚀")
print(f"🔧 DEBUG Mode: {DEBUG}")
print(f"🔑 Using Development SECRET_KEY: {'Yes (from .env)' if os.environ.get('DJANGO_SECRET_KEY_DEV') else 'Yes (Default Unsafe)'}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
print(f"🔗 CORS Allowed Origins: {CORS_ALLOWED_ORIGINS}")
print(f"🔑 CORS Allow Credentials: {CORS_ALLOW_CREDENTIALS}")
print("-" * 10 + " DB CONFIG " + "-" * 10)
print(f"  DB Choice (.env): {DB_ENGINE_CHOICE}")
print(f"  Engine: {DATABASES['default'].get('ENGINE', '').split('.')[-1]}")
print(f"  Name: {DATABASES['default'].get('NAME')}")
if DATABASES['default'].get('ENGINE') != 'django.db.backends.sqlite3':
    print(f"  Host: {DATABASES['default'].get('HOST')}")
    print(f"  User: {DATABASES['default'].get('USER') if DATABASES['default'].get('USER') else '(Trusted Connection)'}")
    print(f"  Port: {DATABASES['default'].get('PORT')}")
    print(f"  Options: {DATABASES['default'].get('OPTIONS')}")
print(f"📂 Media Root: {MEDIA_ROOT}")
print(f"🔍 SQL_DEBUG: {'Enabled' if SQL_DEBUG else 'Disabled'} (Log Level: {LOGGING['loggers']['django.db.backends']['level']})")
print(f"🗣️ Language Code: {LANGUAGE_CODE}")
print(f"⏰ Time Zone: {TIME_ZONE}")
print("=" * 50)