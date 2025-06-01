# src/core/views/tenant_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser # O un permiso de "PlatformAdmin"

from src.core.models import Tenant
from src.core.serializers import TenantSerializer
from django_filters.rest_framework import DjangoFilterBackend

class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Tenants (Empresas Cliente).
    Solo accesible por administradores de la plataforma.
    """
    queryset = Tenant.objects.all().order_by('name')
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser] # O un permiso como IsPlatformAdmin
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'name': ['exact', 'icontains'],
        'is_active': ['exact'],
    }

    # perform_create: Podrías añadir lógica aquí si al crear un Tenant
    # también se debe crear un primer usuario administrador para ese Tenant.
    # Esto se haría mejor en un TenantService.
    # def perform_create(self, serializer):
    #     tenant = serializer.save()
    #     # tenant_service.create_initial_admin_for_tenant(tenant, admin_user_data)