# config/settings/base.py
import os
from pathlib import Path
from datetime import timedelta
import json # Importante para DB_OPTIONS

# BASE_DIR apunta al directorio raíz del proyecto (dloub_platform)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASES se definirán completamente en
# development.py o production.py leyendo de os.environ.
# Aquí solo ponemos placeholders o lógica común.

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY_BASE', 'placeholder-secret-key-base') # Fallback muy genérico
DEBUG = False # Por defecto, DEBUG es False. Se activa en development.py
ALLOWED_HOSTS = [] # Se llena en development.py o production.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist', # Para JWT_BLACKLIST_AFTER_ROTATION
    'django_filters',
    'corsheaders',
    'django_countries',
    'storages',

    # Mis Apps (Asegúrate que los nombres de AppConfig sean correctos)
    'src.core.apps.CoreConfig',
    'src.ds_owari.apps.DsOwariConfig',
    'src.modules.crm.apps.CrmConfig',
    'src.modules.dashboard_module.apps.DashboardModuleConfig',
    'src.modules.finances.apps.FinancesConfig',
    'src.modules.project_management.apps.ProjectManagementConfig',
    # 'src.modules.service_catalog_management.apps.ServiceCatalogManagementConfig', # Descomenta si existe
    # 'src.shared_utils.apps.SharedUtilsConfig', # Descomenta si existe
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'src.core.middlewares.CurrentUserMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database (Placeholder - La configuración real estará en development.py/production.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_placeholder_never_used.sqlite3', # Para que Django no se queje
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'core.CustomUser' # 'core' es el label de CoreConfig

LANGUAGE_CODE = os.environ.get('DJANGO_LANGUAGE_CODE', 'es') # Cambiado default a 'es'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# STATIC_ROOT se define en production.py (para collectstatic)
# STATICFILES_DIRS = [BASE_DIR / "global_static"] # Si tienes estáticos globales

MEDIA_URL = '/media/'
# MEDIA_ROOT se define en development.py y production.py

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': int(os.environ.get('DJANGO_PAGE_SIZE', 20)), # Default a 20 si no está en .env
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # BrowsableAPIRenderer se añadirá condicionalmente en development.py
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': os.environ.get('JWT_ROTATE_REFRESH_TOKENS', 'True').lower() in ('true', '1', 't'),
    'BLACKLIST_AFTER_ROTATION': os.environ.get('JWT_BLACKLIST_AFTER_ROTATION', 'True').lower() in ('true', '1', 't'),
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': None, # Se establecerá en dev/prod con la SECRET_KEY del entorno
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}

# CORS (valores por defecto, se sobreescriben en dev/prod)
CORS_ALLOW_CREDENTIALS = False # Default a False
CORS_ALLOWED_ORIGINS = [] # Se llena desde .env en dev/prod

# Logging (Configuración base más detallada)
LOGGING_LEVEL_ROOT = os.environ.get('DJANGO_ROOT_LOG_LEVEL', 'INFO')
LOGGING_LEVEL_DJANGO = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')
LOGGING_LEVEL_DB_BACKENDS = os.environ.get('DJANGO_DB_BACKENDS_LOG_LEVEL', 'INFO') # Para queries
LOGGING_LEVEL_SRC = os.environ.get('SRC_LOG_LEVEL', 'INFO') # Para tus apps

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {name} [{module}:{lineno}] {message}', 'style': '{'},
        'simple': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'},
        'django.server': {'()': 'django.utils.log.ServerFormatter', 'format': '[{server_time}] {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'django.server': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'django.server'},
    },
    'root': {'handlers': ['console'], 'level': LOGGING_LEVEL_ROOT},
    'loggers': {
        'django': {'handlers': ['console'], 'level': LOGGING_LEVEL_DJANGO, 'propagate': False},
        'django.server': {'handlers': ['django.server'], 'level': 'INFO', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False}, # Loguear errores de request
        'django.db.backends': {'handlers': ['console'], 'level': LOGGING_LEVEL_DB_BACKENDS, 'propagate': False},
        'src': {'handlers': ['console'], 'level': LOGGING_LEVEL_SRC, 'propagate': False},
    },
}

# File Storage (Defaults, se sobreescribe en dev/prod si se usa S3/Azure)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'