#src/modules/project_management/apps.py

from django.apps import AppConfig

class ProjectManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.modules.project_management' # Ruta completa para Django
    verbose_name = "Module: Project Management"
    label = 'app_project_management' # nombre m�s descriptivo
    def ready(self):
        try:
            import src.modules.project_management.signals # Asume que la app se llama as� en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendr�n se�ales inicialmente
