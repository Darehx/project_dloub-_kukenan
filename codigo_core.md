# src/core/__init__.py
```
python
# src/core/__init__.py
# Este archivo puede estar vacío o definir el default_app_config
# default_app_config = 'src.core.apps.CoreConfig' # Opcional, Django lo detecta bien con la AppConfig
```
# src/core/admin.py
```
python
from django.contrib import admin

# Register your models here.
```
# src/core/apps.py
```
python
# src/core/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.core'  # O solo 'core' si no pones 'src.' en INSTALLED_APPS
    label = 'core'     # Esta etiqueta es la que usa AUTH_USER_MODEL='core.CustomUser'
    verbose_name = _("Core Application")

    def ready(self):
        # Importar y conectar señales si las tienes definidas en core.signals
        try:
            import src.core.signals  # noqa F401
        except ImportError:
            pass
        
        # Si tienes extensiones al modelo User (como los métodos de roles) que quieres
        # añadir al cargar la app, puedes hacerlo aquí.
        # Por ejemplo, si tienes un archivo src/core/auth_extensions.py:
        # try:
        #     import src.core.auth_extensions # noqa F401
        # except ImportError:
        #     pass
```
# src/core/middlewares.py
```
python
# src/core/middlewares.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """
    Retorna el usuario autenticado actual desde thread local storage.
    Retorna None si no hay usuario o no está autenticado.
    """
    user = getattr(_thread_locals, 'user', None)
    # Opcionalmente, puedes verificar si el usuario es anónimo si eso importa
    # if user and user.is_anonymous:
    #     return None
    return user

def get_current_request():
    """
    Retorna el request actual desde thread local storage.
    """
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        # Almacenar el usuario solo si está autenticado
        # Si usas request.user directamente, puede ser AnonymousUser
        _thread_locals.user = getattr(request, 'user', None)
        
        response = self.get_response(request)
        
        # Limpiar después de que la petición se complete (opcional pero buena práctica)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response
```
# src/core/models.py
```
python
from django.db import models

# Create your models here.
```
# src/core/permissions.py
```
python

```
# src/core/signals.py
```
python

```
# src/core/tests.py
```
python
from django.test import TestCase

# Create your tests here.
```
# src/core/urls.py
```
python
from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views # o from .views.file_views import ...

# router = DefaultRouter()
# router.register(r'example', views.ExampleViewSet, basename='example')

app_name = 'core'

urlpatterns = [
    # path('', include(router.urls)),
]
```
# src/core/views.py
```
python
from django.shortcuts import render

# Create your views here.
```
# src/core/models/__init__.py
```
python
# src/core/models/__init__.py
from .tenant import Tenant
from .user import CustomUser
from .role import UserRole, UserProfile, UserRoleAssignment
from .audit import AuditLog
from .notification import Notification

__all__ = [
    'Tenant',
    'CustomUser',
    'UserRole',
    'UserProfile',
    'UserRoleAssignment',
    'AuditLog',
    'Notification',
]
```
# src/core/models/audit.py
```
python
# src/core/models/audit.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class AuditLog(models.Model):
    """Registro de auditoría de acciones importantes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("User")
    )
    # Opcional: Si las acciones de auditoría son específicas del tenant
    # tenant = models.ForeignKey(
    #    'core.Tenant',
    #    on_delete=models.SET_NULL, # O CASCADE
    #    null=True, blank=True,
    #    related_name='audit_logs'
    # )
    action = models.CharField(
        _("Action"),
        max_length=255,
        help_text=_("Description of the action performed")
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    
    # Para identificar el objeto afectado
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Content Type")
    )
    object_id = models.PositiveIntegerField(
        _("Object ID"),
        null=True, blank=True
    )
    object_repr = models.CharField(
        _("Object Representation"),
        max_length=200,
        blank=True
    )
    # from django.contrib.contenttypes.fields import GenericForeignKey
    # content_object = GenericForeignKey('content_type', 'object_id') # Si quieres una relación genérica directa

    details = models.JSONField(
        _("Details"),
        default=dict,
        blank=True,
        help_text=_("Additional details in JSON format (e.g., changed fields)")
    )
    ip_address = models.GenericIPAddressField(
        _("IP Address"),
        null=True, blank=True
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")

    def __str__(self):
        user_str = self.user.get_username() if self.user else _("System")
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else 'N/A'
        return f"{timestamp_str} - {user_str}: {self.action}"

    @property
    def target(self):
        """Devuelve el objeto real al que se refiere el log, si es posible."""
        if self.content_type and self.object_id:
            try:
                return self.content_type.get_object_for_this_type(pk=self.object_id)
            except self.content_type.model_class().DoesNotExist:
                return None
        return None
```
# src/core/models/notification.py
```
python
# src/core/models/notification.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """Notificaciones para usuarios."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Se resolverá a 'core.CustomUser'
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("User")
    )
    # Opcional: Si las notificaciones son específicas del tenant
    # tenant = models.ForeignKey(
    #    'core.Tenant',
    #    on_delete=models.CASCADE, # Si el tenant se borra, sus notificaciones también
    #    null=True, blank=True, # Si algunas notificaciones son globales
    #    related_name='notifications'
    # )
    message = models.TextField(_("Message"))
    read = models.BooleanField(_("Read"), default=False, db_index=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    link = models.URLField(
        _("Link"),
        null=True, blank=True,
        help_text=_("Relevant link (e.g., to an order, task)")
    )
    # Opcional: Tipo de notificación para filtrado o iconos
    # NOTIFICATION_TYPES = [('info', 'Information'), ('alert', 'Alert'), ('task', 'Task Update')]
    # notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')

    # Opcional: Para notificaciones relacionadas con un objeto específico
    # content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    # object_id = models.PositiveIntegerField(null=True, blank=True)
    # from django.contrib.contenttypes.fields import GenericForeignKey
    # content_object = GenericForeignKey('content_type', 'object_id')


    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        status = _("[Read]") if self.read else _("[Unread]")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        return f"Notification for {username} {status}: {self.message[:50]}..."

    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])

    def mark_as_unread(self):
        if self.read:
            self.read = False
            self.save(update_fields=['read'])
```
# src/core/models/role.py
```
python
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
```
# src/core/models/tenant.py
```
python
# src/core/models/tenant.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Tenant(models.Model):
    """
    Representa una empresa cliente (Tenant) en el sistema SaaS.
    Cada Tenant tendrá sus propios datos aislados en los módulos.
    """
    name = models.CharField(
        _("Company Name"),
        max_length=255,
        unique=True,
        help_text=_("Official name of the tenant company.")
    )
    # slug = models.SlugField(unique=True, help_text=_("Short unique identifier for URLs, etc.")) # Opcional
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Designates whether this tenant is active and can use the system.")
    )
    # Podrías añadir más campos como:
    # plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True)
    # domain = models.CharField(max_length=253, unique=True, null=True, blank=True) # Para subdominios por tenant
    # admin_user = models.ForeignKey( # El primer usuario admin del tenant
    #    settings.AUTH_USER_MODEL, # Se resolverá a CustomUser
    #    on_delete=models.SET_NULL,
    #    null=True, blank=True,
    #    related_name='administered_tenants'
    # )

    class Meta:
        verbose_name = _("Tenant Company")
        verbose_name_plural = _("Tenant Companies")
        ordering = ['name']

    def __str__(self):
        return self.name
```
# src/core/models/user.py
```
python
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
        # Pero si quieres que los "admins" de un Tenant sean también superusuarios *de ese tenant*,\n
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
    # Es esos se definen y se añaden a la clase User en `src/core/signals/__init__.py` o
    # en un archivo `src/core/auth_extensions.py` que se importa en `core.apps.CoreConfig.ready()`.
    # Esto es para mantener el modelo User más limpio y evitar importaciones circulares.

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['username']

    def __str__(self):
        return self.username # o self.email si es el USERNAME_FIELD

    # Puedes añadir otros métodos específicos para tu CustomUser aquí
```
# src/core/serializers/__init__.py
```
python

```
# src/core/serializers/auth.py
```
python

```
# src/core/serializers/role.py
```
python

```
# src/core/serializers/tenant.py
```
python

```
# src/core/serializers/user.py
```
python

```
# src/core/services/__init__.py
```
python

```
# src/core/services/auth_service.py
```
python

```
# src/core/services/tenant_service.py
```
python

```
# src/core/tests/__init__.py
```
python

```
# src/core/views/__init__.py