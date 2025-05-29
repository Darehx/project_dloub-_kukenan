# src/core/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.core'  # O solo 'core' si no pones 'src.' en INSTALLED_APPS
    label = 'core'     # Esta etiqueta es la que usa AUTH_USER_MODEL='core.CustomUser'
    verbose_name = _("Core Application")

    def ready(self):
        # Importar y conectar señales si las tienes definidas en core.signals
        try:
            import src.core.signals  # noqa F401
        except ImportError:
            pass
        
        # Si tienes extensiones al modelo User (como los métodos de roles) que quieres
        # añadir al cargar la app, puedes hacerlo aquí.
        # Por ejemplo, si tienes un archivo src/core/auth_extensions.py:
        # try:
        #     import src.core.auth_extensions # noqa F401
        # except ImportError:
        #     pass