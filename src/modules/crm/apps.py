from django.apps import AppConfig

class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.modules.crm' # Ruta completa para Django
    label = 'app_crm'
    verbose_name = "Module: Crm"

    def ready(self):
        try:
            import src.modules.crm.signals # Asume que la app se llama as� en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendr�n se�ales inicialmente


