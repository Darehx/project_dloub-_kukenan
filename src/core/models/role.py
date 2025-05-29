# src/core/models/role.py
import logging
from django.db import models
from django.conf import settings # Para settings.AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Importa tus constantes de roles de un lugar centralizado si las tienes
# from ...shared_utils.constants import Roles # Ejemplo si las mueves a shared_utils
# O define la clase Roles aquí o impórtala de donde esté.
# Por ahora, asumimos que estará en un archivo roles.py dentro de 'core' o 'shared_utils'
# from .roles_definitions import SystemRoles # Suponiendo un archivo roles_definitions.py

logger = logging.getLogger(__name__)

class UserRole(models.Model):
    """Define los roles disponibles en la aplicación (Primarios y Secundarios)."""
    # Considerar si este modelo debe estar asociado a un Tenant o es global.
    # Si los roles son específicos por Tenant, añadir ForeignKey a Tenant.
    # Por ahora, lo mantendremos global como en el original.
    # tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, null=True, blank=True, related_name='roles')

    name = models.CharField(
        _("Internal Name"), max_length=50, unique=True, # Podría no ser único si es por tenant
        help_text=_("Short internal alias (e.g., 'dev', 'mktg_manager'). Use constants.")
    )
    display_name = models.CharField(
        _("Display Name"), max_length=100,
        help_text=_("User-friendly name shown in interfaces.")
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    # is_system_role = models.BooleanField(_("Is System Role"), default=False, help_text="System roles cannot be deleted by tenants.")
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Role")
        verbose_name_plural = _("User Roles")
        ordering = ['display_name']
        # unique_together = [['tenant', 'name']] # Si los roles son por tenant

    def __str__(self):
        # if self.tenant:
        #     return f"{self.display_name} ({self.tenant.name})"
        return self.display_name

class UserProfile(models.Model):
    """Extiende el modelo User para almacenar el rol principal obligatorio y otra info de perfil."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile',
        verbose_name=_("User")
    )
    primary_role = models.ForeignKey(
        UserRole,
        on_delete=models.PROTECT, # Proteger para no borrar un rol si está asignado
        null=True, # Permitir null temporalmente para la señal post_save de User, o si no es obligatorio al inicio
        blank=True, # Si no es estrictamente obligatorio al crear el perfil
        related_name='primary_users',
        verbose_name=_("Primary Role"),
        help_text=_("The main role defining the user's core function or access level.")
    )
    # Otros campos de perfil que no estén en CustomUser
    # phone_number = models.CharField(max_length=30, blank=True, null=True)
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        role_name = self.primary_role.display_name if self.primary_role else _("No primary role")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        return f"Profile for {username} ({role_name})"

    def clean(self):
        # Si el rol primario es obligatorio después de la creación inicial, puedes añadir validación aquí.
        # if not self.primary_role_id:
        #     raise ValidationError({'primary_role': _('A primary role must be assigned to the profile.')})
        pass


class UserRoleAssignment(models.Model):
    """Vincula un Usuario con un Rol SECUNDARIO (Acceso) específico."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.CASCADE,
        related_name='secondary_role_assignments',
        verbose_name=_("User")
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='user_assignments', # Cambiado de 'secondary_assignments'
        verbose_name=_("Secondary Role/Access")
    )
    # Si los roles son por tenant, y las asignaciones también, añadir ForeignKey a Tenant.
    # tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, related_name='role_assignments')
    
    is_active = models.BooleanField(_("Assignment Active"), default=True)
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        unique_together = ('user', 'role') # Podría ser ('tenant', 'user', 'role') si es por tenant
        verbose_name = _("Secondary Role / Access Assignment")
        verbose_name_plural = _("Secondary Role / Access Assignments")
        ordering = ['user__username', 'role__display_name']

    def __str__(self):
        status = _("Active") if self.is_active else _("Inactive")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        role_name = self.role.display_name if hasattr(self, 'role') else 'N/A'
        return f"{username} - Access: {role_name} ({status})"

    def clean(self):
        if self.user_id and self.role_id:
            try:
                # Evitar asignar un rol secundario si ya es el primario del usuario
                user_profile = UserProfile.objects.filter(user_id=self.user_id).first()
                if user_profile and user_profile.primary_role_id == self.role_id:
                    raise ValidationError({
                        'role': _('This role is already assigned as the primary role for this user.')
                    })
            except UserProfile.DoesNotExist:
                logger.warning(f"UserProfile not found for user_id {self.user_id} during UserRoleAssignment validation.")
            except Exception as e:
                 logger.warning(f"Exception during UserRoleAssignment.clean validation: {e}")