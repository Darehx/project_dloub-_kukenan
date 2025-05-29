# src/modules/finances/apps.py
from django.apps import AppConfig

class FinancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.modules.finances'
    label = 'app_finances' # <--- ETIQUETA AÑADIDA/CONFIRMADA
    verbose_name = "Module: Finances"

    def ready(self):
        try:
            import src.modules.finances.signals
        except ImportError:
            pass