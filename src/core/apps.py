# src/core/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
 # Añadir extensiones al modelo User # <--- Comentario un poco fuera de lugar aquí
from django.conf import settings # <--- Necesario para AUTH_USER_MODEL
from django.contrib.auth import get_user_model # <--- Necesario para get_user_model()

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # name = 'src.core'  # O solo 'core' si no pones 'src.' en INSTALLED_APPS
    # ^^^^ ESTE ES EL IMPORTANTE para INSTALLED_APPS
    # Si en INSTALLED_APPS pones 'src.core.apps.CoreConfig' o 'src.core',
    # Django sabe que esta es la app 'core'.
    # El `name` DEBERÍA ser 'src.core' si tus módulos están bajo `src/` y quieres
    # importar como `from src.core.models import ...` consistentemente.
    name = 'src.core'

    label = 'core'     # Esta etiqueta es la que usa AUTH_USER_MODEL='core.CustomUser'
    # ^^^^ CORRECTO. El `label` es lo que se usa para el prefijo en AUTH_USER_MODEL
    # si tu modelo CustomUser está definido dentro de esta app 'core'.

    verbose_name = _("Core Application")

    def ready(self):
        # Importar y conectar señales si las tienes definidas en core.signals
        try:
            import src.core.signals  # noqa F401
        except ImportError:
            pass # Es bueno manejar esto, aunque idealmente el archivo siempre existirá.

        # Si tienes extensiones al modelo User (como los métodos de roles) que quieres
        # añadir al cargar la app, puedes hacerlo aquí.
        # Por ejemplo, si tienes un archivo src/core/auth_extensions.py:
        # try:
        #     import src.core.auth_extensions # noqa F401
        # except ImportError:
        #     pass

        # Añadir métodos de roles al modelo de usuario si es necesario
        # Esto es útil si tienes un modelo de usuario personalizado y quieres añadirle
        # métodos adicionales relacionados con roles o permisos.
        # Verifica si el modelo de usuario es el personalizado

        # El `if settings.AUTH_USER_MODEL == 'core.CustomUser':` estaba fuera del método `ready()`.
        # DEBE estar DENTRO de `ready()` porque `get_user_model()` solo funciona
        # después de que todas las apps estén cargadas.
        if settings.AUTH_USER_MODEL == f'{self.label}.CustomUser': # Más robusto usar self.label
            ActualUserModel = get_user_model()
            # Importar y llamar a una función que añada los métodos
            # Asumimos que auth_extensions.py está en el mismo directorio que apps.py (src/core/)
            try:
                from . import auth_extensions # El punto es crucial aquí para import relativo
                auth_extensions.add_user_role_methods(ActualUserModel)
            except ImportError:
                # Considera loggear un warning si auth_extensions.py es esperado
                print(f"ADVERTENCIA: src.core.auth_extensions.py no encontrado. No se añadieron métodos de roles al User.")
            except AttributeError:
                # Esto podría pasar si auth_extensions.py no tiene la función add_user_role_methods
                print(f"ADVERTENCIA: La función 'add_user_role_methods' no se encontró en src.core.auth_extensions.py.")