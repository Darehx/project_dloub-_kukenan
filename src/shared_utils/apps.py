from django.apps import AppConfig

class SharedUtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.shared_utils' # Ruta completa para Django
    verbose_name = "Shared Utils"

    def ready(self):
        try:
            import src.shared_utils.signals # Asume que la app se llama así en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendrán señales inicialmente
