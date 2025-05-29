# config/settings/base.py

from pathlib import Path
import os
from datetime import timedelta

# Idealmente, python-dotenv carga el .env en manage.py, wsgi.py, y asgi.py
# from dotenv import load_dotenv
# load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env') # Asegura que la ruta al .env sea correcta

BASE_DIR = Path(__file__).resolve().parent.parent.parent # Raíz del proyecto (donde está manage.py)

# SECRET_KEY y DEBUG se definirán en development.py o production.py
# ALLOWED_HOSTS también

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
    'django_filters',
    'corsheaders',
    'django_countries',
    'storages',    # Para django-storages (Azure, S3, etc.)

    # Mis Apps 
    'src.core.apps.CoreConfig',
    'src.modules.crm.apps.CrmConfig',
    'src.modules.finances.apps.FinancesConfig', 
    'src.modules.project_management.apps.ProjectManagementConfig', # Ejemplo
    'src.ds_owari.apps.DsOwariConfig', # Ejemplo
    #'src.shared_utils.apps.SharedUtilsConfig', # Si la tienes como app

    # drf_spectacular o drf_yasg para documentación API (opcional pero recomendado)
    # 'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Debe ir antes de CommonMiddleware usualmente
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf_ViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'src.core.middlewares.CurrentUserMiddleware', # Middleware para obtener el usuario actual
    
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Si tienes plantillas a nivel de proyecto
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
ASGI_APPLICATION = 'config.asgi.application' # Si usas canales o ASGI

# Database (Placeholder, se define en development.py y production.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_placeholder.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'core.CustomUser'  # 'core' aquí se refiere al 'label' de CoreConfig

# Internacionalización
LANGUAGE_CODE = os.environ.get('DJANGO_LANGUAGE_CODE', 'es-es') # ej. 'es-es', 'en-us'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True # Muy recomendado para manejo de fechas y horas

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# STATIC_ROOT se define en production.py
# STATICFILES_DIRS = [BASE_DIR / "static_global"] # Si tienes estáticos globales fuera de apps

# Media files (Archivos subidos por los usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / os.environ.get('DJANGO_MEDIA_ROOT_BASE', 'mediafiles_base_placeholder')
# MEDIA_ROOT se sobreescribe en development.py y production.py

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication', # Para el Browsable API si es necesario
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Default a requerir autenticación
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': int(os.environ.get('DJANGO_PAGE_SIZE', 25)),
    'DEFAULT_RENDERER_CLASSES': ( # Asegurar JSON como default primario
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer', # Se añade en development.py
    ),
    # 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', # Para drf-spectacular
}

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 1))),
    'ROTATE_REFRESH_TOKENS': os.environ.get('JWT_ROTATE_REFRESH_TOKENS', 'True').lower() in ('true', '1', 't'),
    'BLACKLIST_AFTER_ROTATION': os.environ.get('JWT_BLACKLIST_AFTER_ROTATION', 'True').lower() in ('true', '1', 't'),
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    # 'SIGNING_KEY': SECRET_KEY, # Se define en dev/prod donde SECRET_KEY está disponible
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id', # Campo en tu CustomUser model
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5), # No relevante si no usas Sliding Tokens
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1), # No relevante si no usas Sliding Tokens
}

# CORS - Configuración base, se sobreescribe en dev/prod
# CORS_ALLOWED_ORIGINS = [] # Lista vacía por defecto, se llena en dev/prod
# CORS_ALLOW_CREDENTIALS = False # False por defecto

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} P{process:d} T{thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG', # El handler puede tener un nivel más bajo que los loggers
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        # 'mail_admins': { # Ejemplo para errores en producción
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'formatter': 'simple',
        # },
        # 'file_info': { # Ejemplo para loguear a archivo
        #     'level': 'INFO',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': BASE_DIR / 'logs/app_info.log',
        #     'maxBytes': 1024 * 1024 * 5,  # 5 MB
        #     'backupCount': 5,
        #     'formatter': 'verbose',
        # },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_ROOT_LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'], # , 'mail_admins' en prod para errores
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'], # Cambiar a 'mail_admins' en producción para errores
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_DB_BACKENDS_LOG_LEVEL', 'INFO'), # Se ajusta en dev si SQL_DEBUG=True
            'propagate': False,
        },
        # Logger para tus aplicaciones en el directorio 'src'
        'src': {
            'handlers': ['console'], # , 'file_info' si quieres loguear src a archivo
            'level': os.environ.get('SRC_LOG_LEVEL', 'INFO'), # Default a INFO, dev puede ponerlo en DEBUG
            'propagate': False, # O True si quieres que 'root' también lo procese
        },
        # Puedes añadir loggers específicos para tus apps si es necesario
        # 'src.core': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG', # Ejemplo específico
        #     'propagate': False,
        # },
    },
}

# Azure Storage (valores por defecto o placeholders, se leen de .env en prod/dev)
# AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME')
# AZURE_ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY')
# AZURE_MEDIA_CONTAINER = os.environ.get('AZURE_MEDIA_CONTAINER', 'media')
# AZURE_STATIC_CONTAINER = os.environ.get('AZURE_STATIC_CONTAINER', 'static')
# DEFAULT_FILE_STORAGE = os.environ.get('DJANGO_DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
# STATICFILES_STORAGE = os.environ.get('DJANGO_STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')