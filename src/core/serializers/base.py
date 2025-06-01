# src/core/serializers/base.py
import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model

# Importar modelos directamente desde core.models (usando el __init__.py)
# No es necesario importar UserProfile o JobPosition aquí si no se usan directamente
# en BasicUserSerializer, ya que CustomUser tendrá los métodos/properties.

logger = logging.getLogger(__name__)
CustomUser = get_user_model() # Esto obtendrá src.core.CustomUser

class BasicUserSerializer(serializers.ModelSerializer):
    """
    Serializer básico para mostrar información del usuario, incluyendo roles.
    Asume que CustomUser tiene properties/métodos como 'primary_role_name',
    'get_secondary_active_role_names', 'get_all_active_role_names', 'is_dragon'.
    Y que el perfil de empleado (si existe) se accede de otra forma o no es parte de este core serializer.
    Si 'job_position_name' dependía de un 'employee_profile' directamente en el User original,
    esa lógica se moverá a un serializer de Empleado en la app 'ds_owari'.
    """
    full_name = serializers.SerializerMethodField(read_only=True)
    primary_role = serializers.CharField(source='primary_role_name', read_only=True, allow_null=True)
    # primary_role_display_name = serializers.CharField(source='primary_role.display_name', read_only=True, allow_null=True) # Si 'primary_role' es el objeto UserRole
    secondary_roles = serializers.ListField(source='get_secondary_active_role_names', read_only=True, child=serializers.CharField())
    all_roles = serializers.ListField(source='get_all_active_role_names', read_only=True, child=serializers.CharField())
    is_dragon_user = serializers.BooleanField(source='is_dragon', read_only=True) # Asume que CustomUser tiene un método is_dragon()
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True, allow_null=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff', # is_staff indica si puede acceder al admin de Django
            'primary_role',
            # 'primary_role_display_name',
            'secondary_roles',
            'all_roles', 'is_dragon_user',
            'tenant_id', 'tenant_name',
        ]

    def get_full_name(self, obj):
        name = obj.get_full_name()
        return name if name else obj.username