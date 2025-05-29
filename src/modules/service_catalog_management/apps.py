from django.apps import AppConfig

class ServiceCatalogManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.modules.service_catalog_management' # Ruta completa para Django
    verbose_name = "Module: Service Catalog Management"

    def ready(self):
        try:
            import src.modules.service_catalog_management.signals # Asume que la app se llama así en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendrán señales inicialmente
