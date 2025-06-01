# src/core/serializers/auth.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .base import BasicUserSerializer # Importar el serializer base

CustomUser = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # El username/email y password son validados por TokenObtainPairSerializer.validate()
        # Aquí solo necesitamos obtener el usuario después de que la validación base pase.
        # Si falla (malas credenciales), super().validate() lanzará AuthenticationFailed.
        
        # La lógica de 'check_password' y 'user.is_active' ya la hace
        # la validación por defecto de TokenObtainPairSerializer.
        # No es necesario replicarla aquí a menos que quieras un mensaje de error customizado
        # antes de que se intente generar el token.

        data = super().validate(attrs) # Obtiene access y refresh tokens

        # 'self.user' es establecido por TokenObtainPairSerializer después de una autenticación exitosa
        user = self.user 
        
        if not user.is_active: # Doble chequeo o si la validación de JWT no lo cubre exactamente como quieres
            raise AuthenticationFailed(_("Your account is inactive."), code="user_inactive")

        # Añadir datos del usuario usando BasicUserSerializer
        # Es importante precargar las relaciones necesarias en la vista o aquí para eficiencia
        # Por ejemplo, en la vista que usa este serializer:
        # user_with_rels = CustomUser.objects.select_related('tenant', 'profile__primary_role') \
        #                                   .prefetch_related('secondary_role_assignments__role') \
        #                                   .get(pk=user.pk)
        # user_data = BasicUserSerializer(user_with_rels).data
        
        # O si no es posible precargar en la vista, hazlo aquí, aunque es menos ideal
        try:
            user_with_rels = CustomUser.objects.select_related(
                'tenant',
                'profile__primary_role'
            ).prefetch_related(
                'secondary_role_assignments__role' # Asume que UserRoleAssignment usa related_name='secondary_role_assignments'
            ).get(pk=user.pk)
            user_data = BasicUserSerializer(user_with_rels).data
        except CustomUser.DoesNotExist:
            # Esto no debería pasar si super().validate() fue exitoso
            raise AuthenticationFailed(_("User not found after authentication."), code="user_not_found_post_auth")
        except Exception as e:
            # Loggear este error
            print(f"Error serializing user data in token obtain: {e}")
            user_data = BasicUserSerializer(user).data # Fallback sin relaciones optimizadas

        data.update({'user': user_data})
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user) # Obtiene el token base con 'user_id'

        # Añadir claims personalizados al token JWT
        # Estos métodos/properties deben existir en tu modelo CustomUser
        token['username'] = user.username
        token['email'] = user.email # Si quieres el email en el token
        token['roles'] = user.get_all_active_role_names # Asume que este método existe y devuelve una lista de strings
        token['primary_role'] = user.primary_role_name # Asume que este property existe
        token['is_dragon'] = user.is_dragon() # Asume que este método existe
        
        if user.tenant:
            token['tenant_id'] = user.tenant.id
            token['tenant_name'] = user.tenant.name
        else:
            token['tenant_id'] = None
            token['tenant_name'] = None
            
        return token