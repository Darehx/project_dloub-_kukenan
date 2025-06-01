# src/core/serializers/role.py
from rest_framework import serializers
from src.core.models import UserRole, UserProfile, UserRoleAssignment # Importa modelos de core
from django.contrib.auth import get_user_model

# Importar BasicUserSerializer si lo necesitas aquí
from .base import BasicUserSerializer

CustomUser = get_user_model()

class UserRoleSerializer(serializers.ModelSerializer):
    """ Serializer para el modelo UserRole. """
    # Opcional: si los roles son por tenant y quieres mostrar info del tenant
    # tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)

    class Meta:
        model = UserRole
        fields = [
            'id', 'name', 'display_name', 'description', 'is_active',
            # 'tenant_name', # si aplica
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        # Si los roles son por tenant y el tenant se asigna automáticamente:
        # extra_kwargs = {'tenant': {'write_only': True, 'required': False}}


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer para gestionar asignaciones de roles secundarios. """
    user_info = BasicUserSerializer(source='user', read_only=True)
    role_info = UserRoleSerializer(source='role', read_only=True)

    # Campos para crear/actualizar (escritura)
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=True
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.filter(is_active=True),
        write_only=True
    )
    # Opcional: si las asignaciones son por tenant y el tenant se asigna
    # tenant_id = serializers.PrimaryKeyRelatedField(source='tenant', queryset=Tenant.objects.all(), write_only=True, required=False)


    class Meta:
        model = UserRoleAssignment
        fields = [
            'id',
            'user', 'user_info',  # user es para write, user_info para read
            'role', 'role_info',  # role es para write, role_info para read
            # 'tenant_id', # si aplica
            'is_active', 'assigned_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_info', 'role_info', 'assigned_at', 'updated_at']

    def validate(self, attrs):
        # Validar que el rol secundario no sea el mismo que el primario del usuario
        user = attrs.get('user')
        role = attrs.get('role')
        if user and role:
            try:
                if user.profile and user.profile.primary_role == role:
                    raise serializers.ValidationError({
                        'role': _('This role is already assigned as the primary role for this user.')
                    })
            except UserProfile.DoesNotExist:
                pass # El perfil podría no existir aún, la señal lo creará.
        return attrs