# src/core/views/auth_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status

# Importar serializers del core
from src.core.serializers import CustomTokenObtainPairSerializer, BasicUserSerializer

CustomUser = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT, usando el serializer customizado.
    Hereda la lógica de manejo de POST de TokenObtainPairView.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny] # Permitir acceso anónimo para el login

class CheckAuthView(APIView):
    """
    Verifica si el usuario actual está autenticado y devuelve sus datos básicos.
    """
    permission_classes = [IsAuthenticated] # Solo para usuarios autenticados

    def get(self, request):
        """
        Devuelve el estado de autenticación y los datos del usuario.
        """
        try:
            # Optimizar la consulta para obtener relaciones necesarias para BasicUserSerializer
            user = CustomUser.objects.select_related(
                'tenant', # Si CustomUser tiene FK directa a Tenant
                'profile__primary_role'
            ).prefetch_related(
                'secondary_role_assignments__role' # Ajustar related_name si es diferente
            ).get(pk=request.user.pk)
        except CustomUser.DoesNotExist:
            # Esto no debería ocurrir si IsAuthenticated funciona y el token es válido
            return Response(
                {"isAuthenticated": False, "user": None, "detail": _("User not found.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except AttributeError as e:
            # Fallback si las relaciones no existen o hay un error (ej. perfil no creado aún)
            # Deberías loggear esta advertencia
            print(f"Advertencia: Error al acceder a relaciones en CheckAuthView para usuario {request.user.pk}: {e}")
            user = request.user # Usar el request.user básico como fallback

        serializer = BasicUserSerializer(user, context={'request': request})
        data = {"isAuthenticated": True, "user": serializer.data}
        return Response(data)

# Podrías añadir aquí vistas para Registro (si no usas UserViewSet),
# Olvido de Contraseña, Cambio de Contraseña, etc.