import os
from pathlib import Path

# Define las aplicaciones principales y los módulos de producto
MAIN_APPS = ['core', 'ds_owari'] # ds_owari al mismo nivel que core
PRODUCT_MODULES = ['crm', 'project_management', 'finances', 'service_catalog_management', 'dashboard_module']
SHARED_UTILS_APP = 'shared_utils' # Aplicación para utilidades compartidas

# Define la subestructura común para la mayoría de las apps/módulos
# Puedes personalizar esto para apps específicas si es necesario
COMMON_APP_SUBDIRS = [
    'models',
    'serializers',
    'views',
    'services',
    'tests',
    'migrations',
]

COMMON_APP_FILES = [
    '__init__.py',
    'admin.py',
    'apps.py',
    'urls.py',
    'permissions.py',
    'signals.py',
]

# Archivos específicos para el subdirectorio 'models'
MODELS_SUBDIR_INIT_FILE = 'models/__init__.py'
# Archivos específicos para otros subdirectorios (si los hubiera)
SERIALIZERS_SUBDIR_INIT_FILE = 'serializers/__init__.py'
VIEWS_SUBDIR_INIT_FILE = 'views/__init__.py'
SERVICES_SUBDIR_INIT_FILE = 'services/__init__.py'
TESTS_SUBDIR_INIT_FILE = 'tests/__init__.py' # Django crea tests.py, pero un __init__.py permite un directorio de pruebas

def create_app_structure(app_path: Path, app_name_for_config: str, is_module: bool = False):
    """Crea la estructura interna para una app o módulo de producto."""
    print(f"\n--- Creating structure for app: {app_path.name} ---")
    app_path.mkdir(parents=True, exist_ok=True)

    # Crear subdirectorios comunes
    for subdir_name in COMMON_APP_SUBDIRS:
        subdir_path = app_path / subdir_name
        subdir_path.mkdir(exist_ok=True)
        # Crear __init__.py en subdirectorios principales para que sean paquetes
        if subdir_name in ['models', 'serializers', 'views', 'services', 'tests', 'migrations']:
            (subdir_path / '__init__.py').touch(exist_ok=True)

    # Crear archivos comunes a nivel de app
    for file_name in COMMON_APP_FILES:
        (app_path / file_name).touch(exist_ok=True)

    # Contenido básico para apps.py
    app_config_name = ''.join(word.capitalize() for word in app_path.name.split('_')) + 'Config'
    apps_py_content = f"""from django.apps import AppConfig

class {app_config_name}(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name_for_config}' # Ruta completa para Django
    verbose_name = "{'Module: ' if is_module else ''}{app_path.name.replace('_', ' ').title()}"

    def ready(self):
        try:
            import {app_name_for_config}.signals # Asume que la app se llama así en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendrán señales inicialmente
"""
    with open(app_path / 'apps.py', 'w') as f:
        f.write(apps_py_content)

    # Contenido básico para urls.py
    urls_py_content = f"""from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views # o from .views.file_views import ...

# router = DefaultRouter()
# router.register(r'example', views.ExampleViewSet, basename='example')

app_name = '{app_path.name}'

urlpatterns = [
    # path('', include(router.urls)),
]
"""
    with open(app_path / 'urls.py', 'w') as f:
        f.write(urls_py_content)

    print(f"Finished structure for app: {app_path.name}")


def main():
    root = Path('.')
    src_root = root / 'src'
    config_root = root / 'config'

    # --- Directorios a Nivel de Proyecto ---
    project_level_dirs = [
        root,
        config_root,
        config_root / 'settings',
        src_root,
        src_root / 'modules', # Contenedor para módulos de producto
    ]

    print("--- Creating project level directories ---")
    for d_path in project_level_dirs:
        d_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {d_path}")

    # --- Archivos a Nivel de Proyecto ---
    project_level_files = [
        root / '.env',
        root / '.gitignore',
        root / 'manage.py', # Este lo crea django-admin startproject
        root / 'pyproject.toml',
        root / 'README.md',
        root / 'Dockerfile', # Opcional
        config_root / '__init__.py',
        config_root / 'settings' / '__init__.py',
        config_root / 'settings' / 'base.py',
        config_root / 'settings' / 'development.py',
        config_root / 'settings' / 'production.py',
        config_root / 'urls.py',
        config_root / 'wsgi.py', # Lo crea django-admin
        config_root / 'asgi.py', # Lo crea django-admin
        src_root / '__init__.py',
        src_root / 'modules' / '__init__.py',
    ]

    print("\n--- Creating project level files ---")
    for f_path in project_level_files:
        # No sobrescribir manage.py, wsgi.py, asgi.py si ya existen por django-admin
        if f_path.name in ['manage.py', 'wsgi.py', 'asgi.py'] and f_path.exists():
            print(f"Skipping existing Django file: {f_path}")
            continue
        if not f_path.exists(): # Solo tocar si no existe para no borrar contenido
            f_path.touch(exist_ok=True)
            print(f"Created file: {f_path}")
        else:
            print(f"File already exists: {f_path}")


    # --- Crear Estructura para Apps Principales ---
    for app_name in MAIN_APPS:
        app_full_path_for_config = f'src.{app_name}' # Cómo se referenciará en INSTALLED_APPS
        create_app_structure(src_root / app_name, app_full_path_for_config)
        # Archivos específicos adicionales para 'core' (ejemplos)
        if app_name == 'core':
            (src_root / app_name / 'models' / 'tenant.py').touch(exist_ok=True)
            (src_root / app_name / 'models' / 'user.py').touch(exist_ok=True)
            (src_root / app_name / 'models' / 'role.py').touch(exist_ok=True)
            (src_root / app_name / 'models' / 'audit.py').touch(exist_ok=True)
            (src_root / app_name / 'models' / 'notification.py').touch(exist_ok=True)

            (src_root / app_name / 'services' / 'tenant_service.py').touch(exist_ok=True)
            (src_root / app_name / 'services' / 'auth_service.py').touch(exist_ok=True)

            (src_root / app_name / 'serializers' / 'tenant.py').touch(exist_ok=True)
            (src_root / app_name / 'serializers' / 'user.py').touch(exist_ok=True)
            (src_root / app_name / 'serializers' / 'auth.py').touch(exist_ok=True)
            (src_root / app_name / 'serializers' / 'role.py').touch(exist_ok=True)


    # --- Crear Estructura para Módulos de Producto ---
    modules_path = src_root / 'modules'
    for module_name in PRODUCT_MODULES:
        module_full_path_for_config = f'src.modules.{module_name}'
        create_app_structure(modules_path / module_name, module_full_path_for_config, is_module=True)

    # --- Crear Estructura para Shared Utils ---
    shared_utils_path = src_root / SHARED_UTILS_APP
    shared_utils_full_path_for_config = f'src.{SHARED_UTILS_APP}'
    create_app_structure(shared_utils_path, shared_utils_full_path_for_config)


    print("\n--- Initial Django project setup (if not already done) ---")
    print("If this is a brand new project, run the following in your terminal (inside 'dloub_platform'):")
    print("1. (If not done) `django-admin startproject config .`")
    print("2. Review `config/settings/base.py` and add your apps to INSTALLED_APPS:")
    print("   Example for core: 'src.core.apps.CoreConfig'")
    print("   Example for crm module: 'src.modules.crm.apps.CrmConfig'")
    print("   Example for ds_owari: 'src.ds_owari.apps.DsOwariConfig'")
    print("3. Configure `config/urls.py` to include your app URLs.")
    print("4. Set `DJANGO_SETTINGS_MODULE=config.settings.development` in your .env or environment.")
    print("5. Run `python manage.py makemigrations` and `python manage.py migrate`")

if __name__ == '__main__':
    # Asegúrate de que el script se ejecute desde el directorio que contendrá 'dloub_platform'
    # o ajusta 'root' para que sea una ruta absoluta o relativa al script.
    # Por simplicidad, este script asume que se ejecuta y 'dloub_platform' se crea en el CWD.
    main()
    print("\nScript finished. Review the created structure.")