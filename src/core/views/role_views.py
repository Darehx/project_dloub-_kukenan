# src/core/views/role_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser # O IsPlatformAdmin

from src.core.models import UserRole, UserRoleAssignment
from src.core.serializers import UserRoleSerializer, UserRoleAssignmentSerializer
from django_filters.rest_framework import DjangoFilterBackend

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Roles de Usuario (UserRole).
    Restringido a administradores de plataforma.
    """
    queryset = UserRole.objects.all().order_by('display_name')
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdminUser] # O IsPlatformAdmin
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'name': ['exact', 'icontains'],
        'display_name': ['exact', 'icontains'],
        'is_active': ['exact'],
        # 'tenant': ['exact', 'isnull'], # Si los roles son por tenant
    }

class UserRoleAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asignaciones de roles secundarios.
    Restringido a administradores de plataforma.
    """
    queryset = UserRoleAssignment.objects.select_related('user', 'role').all().order_by('user__username')
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [IsAdminUser] # O IsPlatformAdmin
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'user__username': ['exact', 'icontains'],
        'role__name': ['exact', 'icontains'],
        'is_active': ['exact'],
        # 'tenant': ['exact'], # Si las asignaciones son por tenant
    }

    # Si necesitas lógica especial al crear/actualizar, por ejemplo,
    # para asegurar que la asignación sea válida para el tenant del usuario.