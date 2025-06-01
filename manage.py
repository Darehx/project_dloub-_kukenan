#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path # Añadido
from dotenv import load_dotenv # Añadido

def main():
    """Run administrative tasks."""
    
    # Cargar .env ANTES de cualquier otra cosa de Django
    # Asume que .env está en el mismo directorio que manage.py
    dotenv_path = Path(__file__).resolve().parent / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        # print(f"INFO (manage.py): .env loaded from {dotenv_path}") # Para depuración
    else:
        print(f"ADVERTENCIA (manage.py): .env file not found at {dotenv_path}")

    # Establecer DJANGO_SETTINGS_MODULE si no está ya definido
    # Puede leer DJANGO_SETTINGS_MODULE del .env que acabamos de cargar
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    # print(f"INFO (manage.py): DJANGO_SETTINGS_MODULE is '{os.environ.get('DJANGO_SETTINGS_MODULE')}'") # Para depuración


    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()