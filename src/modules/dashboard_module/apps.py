from django.apps import AppConfig

class DashboardModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.modules.dashboard_module' # Ruta completa para Django
    verbose_name = "Module: Dashboard Module"

    def ready(self):
        try:
            import src.modules.dashboard_module.signals # Asume que la app se llama así en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendrán señales inicialmente
