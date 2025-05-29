# src/core/models/user.py
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Para AUTH_USER_MODEL en otros modelos

# Importar Tenant aquí para evitar importación circular si CustomUser lo usa directamente
# from .tenant import Tenant # Descomentar si añades FK a Tenant directamente en CustomUser

class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        # username no es obligatorio si usas email para login, pero AbstractUser lo requiere.
        # Si username es None y email existe, podrías autogenerar username del email
        if not username:
             if email:
                 username = email.split('@')[0] # O una lógica más robusta
             else:
                 raise ValueError(_('The Username field must be set if email is not provided'))

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # Superusuarios del sistema Dloub+ (Owari/Doruain) no necesariamente pertenecen a un Tenant cliente.
        # Pero si quieres que los "admins" de un Tenant sean también superusuarios *de ese tenant*,
        # necesitarías una lógica de roles más granular.
        # extra_fields.setdefault('tenant', None) # Opcional, si superusuarios no tienen tenant
        
        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Modelo de Usuario Personalizado.
    Hereda de AbstractUser para mantener la mayoría de los campos y la gestión de Django.
    """
    email = models.EmailField(_('email address'), unique=True) # Hacer email único y principal para login

    # Opcional: Añadir ForeignKey a Tenant
    # Un usuario puede pertenecer a una TenantCompany (si es un usuario de un cliente SaaS)
    # o no pertenecer a ninguna (si es un empleado de Owari/Doruain o un superadmin global).
    tenant = models.ForeignKey(
        'core.Tenant', # Referencia string para evitar importación circular temprana
        on_delete=models.SET_NULL, # O CASCADE si un usuario no puede existir sin tenant (cuidado con superadmins)
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_("Tenant Company"),
        help_text=_("The tenant company this user belongs to, if any.")
    )

    # Si usas email como username:
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username'] # username seguiría siendo necesario para create_superuser si no lo generas

    objects = CustomUserManager()

    # Los related_name para groups y user_permissions se pueden dejar como están si
    # no hay riesgo de colisión o si se manejan con cuidado.
    # Si quieres ser explícito para evitar cualquier posible colisión futura con el auth.User original:
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_groups", # Cambiado
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_permissions", # Cambiado
        related_query_name="customuser",
    )

    # Aquí NO añadimos los métodos/properties de roles (primary_role, has_role, etc.)
    # Esos se definen y se añaden a la clase User en `src/core/signals/__init__.py` o
    # en un archivo `src/core/auth_extensions.py` que se importa en `core.apps.CoreConfig.ready()`.
    # Esto es para mantener el modelo User más limpio y evitar importaciones circulares.

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['username']

    def __str__(self):
        return self.username # o self.email si es el USERNAME_FIELD

    # Puedes añadir otros métodos específicos para tu CustomUser aquí