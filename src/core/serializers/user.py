# src/core/serializers/user.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base import BasicUserSerializer # Importar el serializer base
from src.core.models import UserProfile, Tenant, UserRole # <--- AÑADE UserRole AQUÍ

CustomUser = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    # ... (código existente sin cambios) ...
    pass # Reemplaza 'pass' con tu código existente para UserCreateSerializer

class UserDetailSerializer(BasicUserSerializer):
    # ... (código existente sin cambios) ...
    pass # Reemplaza 'pass' con tu código existente para UserDetailSerializer


# --- Serializer para UserProfile ---
class UserProfileSerializer(serializers.ModelSerializer):
    primary_role_name = serializers.CharField(source='primary_role.display_name', read_only=True, allow_null=True)

    # Campo para actualizar el rol primario enviando el ID del UserRole
    primary_role_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.filter(is_active=True), # Ahora UserRole está definido
        source='primary_role',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'user_id',
            'primary_role_id',
            'primary_role_name',
            # Añadir otros campos del UserProfile aquí
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at', 'primary_role_name']