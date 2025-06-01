# src/core/views/user_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, viewsets
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend


# Importar serializers y modelos del core
from src.core.serializers import (
    BasicUserSerializer,
    UserCreateSerializer,
    UserDetailSerializer, # Usar este para retrieve/list/update
    UserProfileSerializer
)
from src.core.models import CustomUser, UserProfile

# Importar permisos personalizados si los tienes
# from .permissions import IsPlatformAdminOrOwningUser # Ejemplo

CustomUser = get_user_model()

class UserMeView(APIView):
    """
    Devuelve los datos del usuario actualmente autenticado.
    Similar a CheckAuthView pero específicamente para /users/me/.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Obtiene y serializa los datos del usuario logueado.
        """
        try:
            user = CustomUser.objects.select_related(
                'tenant',
                'profile__primary_role'
            ).prefetch_related(
                'secondary_role_assignments__role'
            ).get(pk=request.user.pk)
        except CustomUser.DoesNotExist:
             return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)
        except AttributeError as e:
             print(f"Advertencia: Error al acceder a relaciones en UserMeView para usuario {request.user.pk}: {e}")
             user = request.user # Fallback

        serializer = UserDetailSerializer(user, context={'request': request}) # Usar UserDetailSerializer
        return Response(serializer.data)

    def patch(self, request):
        """
        Permite al usuario actualmente autenticado actualizar sus propios datos (limitados).
        Por ejemplo, first_name, last_name. La actualización de email o password
        debería tener endpoints separados y más seguros.
        """
        user = request.user
        # Usar un serializer específico para actualizar el perfil del usuario 'me'
        # que solo permita modificar ciertos campos.
        # Por ahora, usaremos UserDetailSerializer con partial=True, pero es mejor uno específico.
        serializer = UserDetailSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Usuarios (CustomUser).
    Generalmente restringido a administradores de plataforma.
    """
    queryset = CustomUser.objects.all().select_related('tenant', 'profile__primary_role').order_by('id')
    permission_classes = [IsAdminUser] # O un permiso más específico como IsPlatformAdmin
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'email': ['exact', 'icontains'],
        'username': ['exact', 'icontains'],
        'is_active': ['exact'],
        'is_staff': ['exact'],
        'tenant': ['exact', 'isnull'], # Filtrar por tenant_id
        'first_name': ['icontains'],
        'last_name': ['icontains'],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        # Para list, retrieve, update, partial_update
        return UserDetailSerializer # Muestra más detalles

    # perform_create está bien por defecto si UserCreateSerializer maneja la creación y hashing.
    # perform_update está bien por defecto.
    # Considerar la actualización de contraseña: debería ser un endpoint @action separado.

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Perfiles de Usuario (UserProfile).
    El 'user' (PK) se usa como lookup_field.
    """
    queryset = UserProfile.objects.select_related('user', 'primary_role').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser] # O permisos más granulares
    lookup_field = 'user' # Usar el ID del usuario para buscar/actualizar el perfil

    # No se permite crear UserProfile directamente, se crea con una señal al crear CustomUser.
    # Así que, probablemente solo necesites retrieve, update, partial_update, list.
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    # Si quieres permitir que un usuario actualice su propio perfil a través de /api/v1/core/profiles/me/
    # necesitarías lógica adicional en get_object o get_queryset. O un endpoint dedicado.