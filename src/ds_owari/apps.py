#src/ds_owari/apps.py
# 
from django.apps import AppConfig

class DsOwariConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.ds_owari' # Ruta completa para Django
    verbose_name = "Ds Owari"
    label = 'app_ds_owari' # nombre m�s descriptivo
    # Este label es importante para evitar conflictos con otras apps que puedan tener el mismo nombre

    def ready(self):
        try:
            import src.ds_owari.signals # Asume que la app se llama as� en INSTALLED_APPS
        except ImportError:
            pass # No todas las apps tendr�n se�ales inicialmente
