# src/core/middlewares.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """
    Retorna el usuario autenticado actual desde thread local storage.
    Retorna None si no hay usuario o no está autenticado.
    """
    user = getattr(_thread_locals, 'user', None)
    # Opcionalmente, puedes verificar si el usuario es anónimo si eso importa
    # if user and user.is_anonymous:
    #     return None
    return user

def get_current_request():
    """
    Retorna el request actual desde thread local storage.
    """
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        # Almacenar el usuario solo si está autenticado
        # Si usas request.user directamente, puede ser AnonymousUser
        _thread_locals.user = getattr(request, 'user', None)
        
        response = self.get_response(request)
        
        # Limpiar después de que la petición se complete (opcional pero buena práctica)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response