# config/settings/development.py

from .base import *  # Importa todo de base.py
import os
import json # Para parsear el JSON de DB_OPTIONS

# Cargar variables de .env si aún no lo han hecho manage.py o wsgi/asgi
# (esto es opcional y depende de tu flujo, pero puede ser útil para scripts)
# from dotenv import load_dotenv
# env_path = BASE_DIR / '.env' # BASE_DIR viene de base.py
# if env_path.exists():
#     load_dotenv(dotenv_path=env_path)
# else:
#     print(f"ADVERTENCIA: Archivo .env no encontrado en {env_path}")


# Configuración de Seguridad para Desarrollo
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY_DEV', 'django_unsafe_dev_secret_key_123!@#DONTUSEINPROD')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS_CSV = os.environ.get('DJANGO_ALLOWED_HOSTS_DEV', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_CSV.split(',') if host.strip()]


# Configuración de Base de Datos para Desarrollo
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE_DEV', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME_DEV', str(BASE_DIR / 'db_dev.sqlite3')), # Default a SQLite
        'USER': os.environ.get('DB_USER_DEV'),
        'PASSWORD': os.environ.get('DB_PASSWORD_DEV'),
        'HOST': os.environ.get('DB_HOST_DEV'),
        'PORT': os.environ.get('DB_PORT_DEV'),
            'OPTIONS': {},
    }
}

db_options_dev_json_str = os.environ.get('DB_OPTIONS_DEV_JSON')
if db_options_dev_json_str:
    try:
        db_options_from_env = json.loads(db_options_dev_json_str)
        DATABASES['default']['OPTIONS'].update(db_options_from_env)
    except json.JSONDecodeError:
        print(f"ADVERTENCIA: DB_OPTIONS_DEV_JSON ('{db_options_dev_json_str}') no es un JSON válido. Se ignorarán estas opciones.")

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    if not os.path.isabs(DATABASES['default']['NAME']):
        DATABASES['default']['NAME'] = str(BASE_DIR / DATABASES['default']['NAME'])
    for key_to_remove in ['USER', 'PASSWORD', 'HOST', 'PORT', 'OPTIONS']:
        DATABASES['default'].pop(key_to_remove, None)
else:
    db_default_config = DATABASES['default']
    for key in ['USER', 'PASSWORD', 'HOST', 'PORT']: # Claves opcionales para algunos motores
        if key in db_default_config and db_default_config[key] is None: # Si es None explícito del .env
            del db_default_config[key]
        elif key in db_default_config and not db_default_config[key] and db_default_config[key] is not None: # Si es cadena vacía
             # Algunos drivers prefieren que no esté la clave si es vacía, otros lo manejan.
             # Considera eliminarla si causa problemas: del db_default_config[key]
             pass # Por ahora, mantenemos cadenas vacías si se especifican así
    if not db_default_config.get('OPTIONS'):
        db_default_config.pop('OPTIONS', None)


# Simple JWT - Sobreescribir SIGNING_KEY para usar la de desarrollo
# (base.py no puede acceder a SECRET_KEY directamente porque se define aquí o en production.py)
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY


# Configuración de Email para Desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER_DEV', 'dev_user@example.com') # Si es necesario para alguna prueba

# Configuración de CORS para Desarrollo
CORS_ALLOWED_ORIGINS_CSV = os.environ.get('CORS_ALLOWED_ORIGINS_DEV', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173')
if CORS_ALLOWED_ORIGINS_CSV:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_CSV.split(',') if origin.strip()]
else:
    CORS_ALLOWED_ORIGINS = []

CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS_DEV', 'True').lower() in ('true', '1', 't')

# Si quieres ser muy permisivo en desarrollo (NO PARA PROD):
# CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS_DEV', 'False').lower() in ('true', '1', 't')
# if CORS_ALLOW_ALL_ORIGINS:
#     CORS_ALLOWED_ORIGINS = [] # Resetear la lista si se permite todo
#     print("ADVERTENCIA DE SEGURIDAD: CORS_ALLOW_ALL_ORIGINS está activado en desarrollo.")


# Media Files para Desarrollo Local
MEDIA_ROOT = BASE_DIR / os.environ.get('DJANGO_MEDIA_ROOT_DEV', 'mediafiles_development')
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT, exist_ok=True)


# Django REST Framework - Renderers para Desarrollo
if DEBUG:
    # Asegurarse de que REST_FRAMEWORK está definido y es un diccionario mutable
    if 'REST_FRAMEWORK' not in globals() or not isinstance(REST_FRAMEWORK, dict):
        REST_FRAMEWORK = {} # Inicializar si no existe o no es un dict de base.py

    # Obtener renderers actuales o un tuple vacío si no está definido
    current_renderers = list(REST_FRAMEWORK.get('DEFAULT_RENDERER_CLASSES', ()))
    
    # Asegurar JSONRenderer como el primero o default
    if 'rest_framework.renderers.JSONRenderer' not in current_renderers:
        current_renderers.insert(0, 'rest_framework.renderers.JSONRenderer')
    
    # Añadir BrowsableAPIRenderer si no está presente
    if 'rest_framework.renderers.BrowsableAPIRenderer' not in current_renderers:
        current_renderers.append('rest_framework.renderers.BrowsableAPIRenderer')
    
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = tuple(current_renderers)

    # Opcional: Añadir SessionAuthentication para el Browsable API
    # current_auth_classes = list(REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', ()))
    # if 'rest_framework_simplejwt.authentication.JWTAuthentication' not in current_auth_classes:
    #     current_auth_classes.insert(0, 'rest_framework_simplejwt.authentication.JWTAuthentication')
    # if 'rest_framework.authentication.SessionAuthentication' not in current_auth_classes:
    #     current_auth_classes.append('rest_framework.authentication.SessionAuthentication')
    # REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = tuple(current_auth_classes)


# Configuración de Logging para Desarrollo
# LOGGING se hereda de base.py. Aquí ajustamos los niveles para desarrollo.
if DEBUG:
    LOGGING['root']['level'] = 'DEBUG'
    
    # Asegurar que las claves de logger existen antes de asignarles nivel
    LOGGING['loggers'].setdefault('src', {})['level'] = 'DEBUG'
    LOGGING['loggers'].setdefault('django', {})['level'] = 'INFO' # Django general más callado
    LOGGING['loggers'].setdefault('django.server', {})['level'] = 'DEBUG' # Servidor de desarrollo más verboso
    LOGGING['loggers'].setdefault('django.request', {})['level'] = 'DEBUG' # Peticiones
    
    db_backends_logger = LOGGING['loggers'].setdefault('django.db.backends', {})
    if os.environ.get('SQL_DEBUG', 'False').lower() in ('true', '1', 't'):
        db_backends_logger['level'] = 'DEBUG'
    else:
        db_backends_logger['level'] = 'INFO'


# Django Debug Toolbar (si la instalas para desarrollo)
# Asegúrate de añadir 'debug_toolbar' a INSTALLED_APPS en base.py o aquí
# if DEBUG:
#     try:
#         import debug_toolbar
#         if 'debug_toolbar' not in INSTALLED_APPS:
#             INSTALLED_APPS += ['debug_toolbar']
#         if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
#             # Insertar después de SessionMiddleware y antes de CommonMiddleware, si es posible
#             # O simplemente añadirlo. La posición exacta puede variar.
#             # CommonMiddleware suele ser un buen punto de referencia.
#             try:
#                 idx_common = MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
#                 MIDDLEWARE.insert(idx_common, 'debug_toolbar.middleware.DebugToolbarMiddleware')
#             except ValueError:
#                 MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        
#         INTERNAL_IPS = [os.environ.get('INTERNAL_IPS_DEV', '127.0.0.1')]
#         # DEBUG_TOOLBAR_CONFIG = { 'SHOW_TOOLBAR_CALLBACK': lambda request: True } # Para mostrar siempre
#     except ImportError:
#         print("ADVERTENCIA: Django Debug Toolbar no está instalada. Para usarla, instálala (`pip install django-debug-toolbar`).")


# Mensajes informativos al iniciar en modo desarrollo
print("========================================================")
print("🚀 DLOUB+ PLATFORM - DEVELOPMENT SETTINGS LOADED 🚀")
print(f"🔧 DEBUG Mode: {DEBUG}")
print(f"🔑 Using Development SECRET_KEY: {'Yes' if SECRET_KEY else 'No (Fallback unsafe key will be used!)'}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
print(f"🔗 CORS Allowed Origins: {CORS_ALLOWED_ORIGINS if CORS_ALLOWED_ORIGINS else 'None (check CORS_ALLOW_ALL_ORIGINS)'}")
# if CORS_ALLOW_ALL_ORIGINS: print("🚨 CORS_ALLOW_ALL_ORIGINS is TRUE 🚨")
print("---------------- DB CONFIG -------------------")
print(f"  Engine: {DATABASES['default'].get('ENGINE')}")
print(f"  Name: {DATABASES['default'].get('NAME')}")
if DATABASES['default'].get('ENGINE') != 'django.db.backends.sqlite3':
    print(f"  Host: {DATABASES['default'].get('HOST', 'N/A')}")
    print(f"  User: {DATABASES['default'].get('USER', 'N/A')}")
    print(f"  Port: {DATABASES['default'].get('PORT', 'N/A')}")
    print(f"  Options: {DATABASES['default'].get('OPTIONS', {})}")
print(f"📂 Media Root: {MEDIA_ROOT}")
if os.environ.get('SQL_DEBUG', 'False').lower() in ('true', '1', 't'):
    print("🔍 SQL_DEBUG: Enabled (Database queries will be logged)")
print("========================================================")