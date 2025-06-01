# src/core/serializers/tenant.py
from rest_framework import serializers
from src.core.models import Tenant

class TenantSerializer(serializers.ModelSerializer):
    """ Serializer para el modelo Tenant. """
    # Opcional: si quieres contar usuarios o mostrar el admin del tenant
    # user_count = serializers.IntegerField(source='users.count', read_only=True)
    # admin_user_email = serializers.EmailField(source='admin_user.email', read_only=True, allow_null=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'is_active',
            # 'user_count', 'admin_user_email', # Si se añaden
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']