¡Entendido! Voy a generar ese archivo `.md` para ti. Este archivo contendrá toda la información clave que hemos discutido y los fragmentos de código que me has proporcionado, estructurado para que pueda tener el contexto completo en una nueva conversación.

Debido a que la longitud de los archivos de código originales es considerable, el archivo `.md` será extenso. Me aseguraré de incluir los delimitadores y comentarios que usaste para separar los archivos de código originales.

Aquí está el contenido que puedes copiar y pegar en un archivo con extensión `.md` (por ejemplo, `dloub_plus_context_transfer.md`):

```markdown
# Dossier del Proyecto Dloub+ para Transferencia de Contexto

## 1. Resumen General del Proyecto y Visión SaaS (Kukenan)

Dloub+ es una plataforma de gestión integral inicialmente concebida para uso interno de las agencias Owari Brand Studio y Doruain. Está diseñada para centralizar y optimizar las operaciones, la gestión de clientes, proyectos, servicios, finanzas y comunicación. La visión a largo plazo es evolucionar Dloub+ a una plataforma SaaS multi-tenant llamada **Dloub+ Kukenan**, que otras empresas podrán contratar para gestionar sus propias operaciones y solicitar servicios directamente a las agencias fundadoras (Owari/Doruain) a través de la misma plataforma.

**Arquitectura Tecnológica General:**
*   **Backend (Dloub+ Núcleo):** Monolito Modular desarrollado con Django y Django REST Framework (DRF) en Python.
*   **Base de Datos:** SQL Server (accedida vía ORM de Django).
*   **Frontend (Dloub+ Kukenan - Portal Cliente):** Aplicación separada (probablemente Next.js/TypeScript/Tailwind CSS) que consumirá la API del backend Dloub+.
*   **Almacenamiento de Archivos:** Azure Blob Storage (u otro), integrado con `django-storages`.
*   **Autenticación:** Basada en Tokens JWT (`djangorestframework-simplejwt`).

**Visión SaaS - Dloub+ Kukenan:**
*   Otras empresas (Tenants) usarán Dloub+ Kukenan (portal cliente) para gestionar sus propias operaciones.
*   Kukenan actúa como un frontend que consume la API de Dloub+ (núcleo).
*   Implicaciones: Multi-Tenancy (modelo `TenantCompany`, aislamiento de datos), API de Dloub+ como producto, módulos contratables.
*   Ejemplo de Flujo: Un cliente en Kukenan solicita un rebranding -> Kukenan hace una llamada API a Dloub+ -> Dloub+ crea el pedido asociado al Tenant correcto -> Owari/Doruain gestiona el pedido internamente.

**Estado Actual del Proyecto:**
Se está en proceso de refactorizar una estructura de backend DRF existente hacia una arquitectura modular multi-tenant. Se ha reconocido que esta estructura es esencial para la mantenibilidad, escalabilidad y la visión SaaS.

---

## 2. Código de la Aplicación Antigua (Antes de la Refactorización)

### 2.1. Modelos, Señales, Permisos y Roles Antiguos (`base_models_api.txt`)

```python
# <CONTENIDO COMPLETO DE base_models_api.txt>
# COMIENZO DE base_models_api.txt
===== models.py =====

# api/models.py

import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, DecimalField, DurationField, ExpressionWrapper, F, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

# --- Importa tus constantes de roles ---
try:
    from .roles import Roles
except ImportError:
    # Define placeholders si el archivo no existe (la app podría fallar si no existen realmente)
    class Roles:
        DRAGON = 'dragon'; ADMIN = 'admin'; MARKETING = 'mktg'; FINANCE = 'fin'
        SALES = 'sales'; DEVELOPMENT = 'dev'; AUDIOVISUAL = 'avps'; DESIGN = 'dsgn'
        SUPPORT = 'support'; OPERATIONS = 'ops'; HR = 'hr'
    print("ADVERTENCIA: api/roles.py no encontrado. Usando roles placeholder.")


# --- Helper para obtener usuario actual (requiere django-crum) ---
try:
    from crum import get_current_user
except ImportError:
    get_current_user = lambda: None
    print("ADVERTENCIA: django-crum no está instalado. Los AuditLogs no registrarán el usuario.")

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

# ==============================================================================
# ------ MODELOS DE GESTIÓN DE USUARIOS, ROLES Y PERFILES ---------------------
# ==============================================================================

class UserRole(models.Model):
    """Define los roles disponibles en la aplicación (Primarios y Secundarios)."""
    name = models.CharField(
        _("Internal Name"), max_length=50, unique=True,
        help_text=_("Short internal alias (e.g., 'dev', 'mktg'). Use constants from roles.py.")
    )
    display_name = models.CharField(
        _("Display Name"), max_length=100,
        help_text=_("User-friendly name shown in interfaces.")
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Role")
        verbose_name_plural = _("User Roles")
        ordering = ['display_name']

    def __str__(self):
        return self.display_name

class UserProfile(models.Model):
    """Extiende el modelo User para almacenar el rol principal obligatorio."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, primary_key=True, related_name='profile', verbose_name=_("User")
    )
    primary_role = models.ForeignKey(
        UserRole, on_delete=models.PROTECT, null=True, blank=False, # null=True temporal para señal
        related_name='primary_users', verbose_name=_("Primary Role"),
        help_text=_("The main mandatory role defining the user's core function.")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        role_name = self.primary_role.display_name if self.primary_role else _("No primary role assigned")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        return f"{username} - Profile ({role_name})"

    def clean(self):
        if not self.primary_role_id:
            raise ValidationError({'primary_role': _('A primary role must be assigned.')})

class UserRoleAssignment(models.Model):
    """Vincula un Usuario con un Rol SECUNDARIO (Acceso) específico."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='secondary_role_assignments', verbose_name=_("User")
    )
    role = models.ForeignKey(
        UserRole, on_delete=models.CASCADE,
        related_name='secondary_assignments', verbose_name=_("Secondary Role/Access")
    )
    is_active = models.BooleanField(_("Assignment Active"), default=True)
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        unique_together = ('user', 'role')
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
                primary_role_id = UserProfile.objects.filter(user_id=self.user_id).values_list('primary_role_id', flat=True).first()
                if primary_role_id and primary_role_id == self.role_id:
                    raise ValidationError({'role': _('This role is already assigned as the primary role for this user.')})
            except Exception as e:
                 logger.warning(f"Excepción durante validación de UserRoleAssignment.clean: {e}")
                 pass

# ==============================================================================
# ---------------------- MODELOS DE LA APLICACIÓN -----------------------------
# ==============================================================================

class Form(models.Model):
    """Modelo para definir estructuras de formularios."""
    name = models.CharField(_("Nombre del Formulario"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Formulario")
        verbose_name_plural = _("Formularios")
        ordering = ['name']

    def __str__(self):
        return self.name

class FormQuestion(models.Model):
    """Pregunta específica dentro de un formulario."""
    form = models.ForeignKey(
        Form, on_delete=models.CASCADE, related_name='questions', verbose_name=_("Formulario")
    )
    question_text = models.TextField(_("Texto de la Pregunta"))
    order = models.PositiveIntegerField(
        _("Orden"), default=0, help_text=_("Orden de aparición en el formulario")
    )
    required = models.BooleanField(_("Requerida"), default=True)

    class Meta:
        ordering = ['form', 'order']
        verbose_name = _("Pregunta de Formulario")
        verbose_name_plural = _("Preguntas de Formularios")

    def __str__(self):
        form_name = self.form.name if hasattr(self, 'form') else 'N/A'
        return f"{form_name} - P{self.order}: {self.question_text[:50]}..."

class FormResponse(models.Model):
    """Respuesta de un cliente a una pregunta de un formulario."""
    customer = models.ForeignKey(
        'Customer', on_delete=models.CASCADE, related_name='form_responses', verbose_name=_("Cliente")
    )
    form = models.ForeignKey(
        Form, on_delete=models.CASCADE, related_name='responses', verbose_name=_("Formulario")
    )
    question = models.ForeignKey(
        FormQuestion, on_delete=models.CASCADE, related_name='responses', verbose_name=_("Pregunta")
    )
    text = models.TextField(_("Respuesta"), help_text=_("Respuesta proporcionada por el cliente"))
    created_at = models.DateTimeField(_("Fecha de Respuesta"), auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'form', 'question')
        ordering = ['created_at']
        verbose_name = _("Respuesta de Formulario")
        verbose_name_plural = _("Respuestas de Formularios")

    def __str__(self):
        customer_str = str(self.customer) if hasattr(self, 'customer') else 'N/A'
        question_str = str(self.question) if hasattr(self, 'question') else 'N/A'
        return f"{_('Respuesta')} de {customer_str} a {question_str}"

class Customer(models.Model):
    """Perfil de un cliente."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile', verbose_name=_("Usuario")
    )
    phone = models.CharField(_("Teléfono"), max_length=30, null=True, blank=True)
    address = models.TextField(_("Dirección"), null=True, blank=True)
    date_of_birth = models.DateField(_("Fecha de Nacimiento"), null=True, blank=True)
    country = CountryField(
        _("País"), blank=True, null=True, help_text=_("País del cliente")
    )
    company_name = models.CharField(
        _("Nombre de Empresa"), max_length=150, blank=True, null=True, help_text=_("Nombre de la empresa (si aplica)")
    )
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    preferred_contact_method = models.CharField(
        _("Método Contacto Preferido"), max_length=20,
        choices=[('email', 'Email'), ('phone', 'Teléfono'), ('whatsapp', 'WhatsApp'), ('other', 'Otro')],
        null=True, blank=True
    )
    brand_guidelines = models.FileField(
        _("Guías de Marca"), upload_to='customers/brand_guidelines/', null=True, blank=True
    )

    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        display_name = self.company_name or self.user.get_full_name() or self.user.username
        email = self.user.email if hasattr(self, 'user') else 'N/A'
        return f"{display_name} ({email})"

class JobPosition(models.Model):
    """Puesto de trabajo dentro de la organización."""
    name = models.CharField(_("Nombre del Puesto"), max_length=50, unique=True)
    description = models.TextField(_("Descripción"), null=True, blank=True)
    permissions = models.JSONField(
        _("Permisos JSON"), default=dict, blank=True, help_text=_("Permisos específicos para este puesto (estructura JSON)")
    )

    class Meta:
        verbose_name = _("Puesto de Trabajo")
        verbose_name_plural = _("Puestos de Trabajo")
        ordering = ['name']

    def __str__(self):
        return self.name

class Employee(models.Model):
    """Perfil de un empleado."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile', verbose_name=_("Usuario")
    )
    hire_date = models.DateField(_("Fecha Contratación"), default=datetime.date.today)
    address = models.TextField(_("Dirección"), null=True, blank=True)
    salary = models.DecimalField(
        _("Salario"), max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    position = models.ForeignKey(
        JobPosition, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employees', verbose_name=_("Puesto")
    )

    class Meta:
        verbose_name = _("Empleado")
        verbose_name_plural = _("Empleados")
        ordering = ['user__first_name', 'user__last_name']

    @property
    def is_active(self):
        return self.user.is_active

    def __str__(self):
        position_name = self.position.name if self.position else _("Sin puesto")
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        display_name = self.user.get_full_name() or self.user.get_username()
        return f"{display_name} ({position_name}) {status}"

class Order(models.Model):
    """Modelo principal para los pedidos de los clientes."""
    STATUS_CHOICES = [
        ('DRAFT', _('Borrador')), ('CONFIRMED', _('Confirmado')), ('PLANNING', _('Planificación')),
        ('IN_PROGRESS', _('En Progreso')), ('QUALITY_CHECK', _('Control de Calidad')),
        ('PENDING_DELIVERY', _('Pendiente Entrega')), ('DELIVERED', _('Entregado')),
        ('CANCELLED', _('Cancelado')), ('ON_HOLD', _('En Espera')),
    ]
    FINAL_STATUSES = ['DELIVERED', 'CANCELLED']

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='orders',
        help_text=_("Cliente que realiza el pedido"), verbose_name=_("Cliente")
    )
    employee = models.ForeignKey(
        Employee, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='managed_orders', help_text=_("Empleado responsable principal"), verbose_name=_("Empleado Asignado")
    )
    date_received = models.DateTimeField(_("Fecha Recepción"), auto_now_add=True)
    date_required = models.DateTimeField(_("Fecha Requerida"), help_text=_("Fecha límite solicitada por el cliente"))
    status = models.CharField(
        _("Estado"), max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    payment_due_date = models.DateTimeField(
        _("Vencimiento Pago"), null=True, blank=True, help_text=_("Fecha límite para el pago (si aplica)")
    )
    note = models.TextField(_("Nota Interna"), null=True, blank=True)
    priority = models.PositiveIntegerField(
        _("Prioridad"), default=3, help_text=_("Prioridad (ej. 1=Alta, 5=Baja)")
    )
    completed_at = models.DateTimeField(
        _("Fecha Completado"), null=True, blank=True, editable=False, help_text=_("Fecha y hora de finalización (status='DELIVERED')")
    )
    total_amount = models.DecimalField(
        _("Monto Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'),
        editable=False, help_text=_("Calculado de OrderService. Actualizado automáticamente.")
    )

    class Meta:
        ordering = ['priority', '-date_received']
        verbose_name = _("Pedido")
        verbose_name_plural = _("Pedidos")

    def __str__(self):
        customer_str = str(self.customer) if hasattr(self, 'customer') else 'N/A'
        return f"{_('Pedido')} #{self.id} ({self.get_status_display()}) - {customer_str}"

    def update_total_amount(self):
        """Calcula y guarda el monto total basado en los servicios asociados."""
        # Se asume que self.services existe en este punto
        total = self.services.aggregate(total=Sum(F('price') * F('quantity')))['total']
        calculated_total = total if total is not None else Decimal('0.00')
        # Actualizar solo si el valor calculado es diferente y el objeto ya existe
        if self.pk and self.total_amount != calculated_total:
             Order.objects.filter(pk=self.pk).update(total_amount=calculated_total)
             self.total_amount = calculated_total # Actualizar instancia en memoria

class ServiceCategory(models.Model):
    """Categorías para agrupar servicios."""
    code = models.CharField(
        _("Código Categoría"), max_length=10, primary_key=True,
        help_text=_("Código corto de la categoría (ej. MKT, DEV)")
    )
    name = models.CharField(
        _("Nombre Categoría"), max_length=100, help_text=_("Nombre descriptivo de la categoría")
    )

    class Meta:
        verbose_name = _("Categoría de Servicio")
        verbose_name_plural = _("Categorías de Servicios")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Campaign(models.Model):
    """Campañas de marketing o promocionales."""
    campaign_code = models.CharField(_("Código Campaña"), max_length=20, primary_key=True)
    campaign_name = models.CharField(_("Nombre Campaña"), max_length=255)
    start_date = models.DateTimeField(_("Fecha Inicio"), help_text=_("Fecha y hora de inicio de la campaña"))
    end_date = models.DateTimeField(
        _("Fecha Fin"), null=True, blank=True, help_text=_("Fecha y hora de fin (opcional)")
    )
    description = models.TextField(_("Descripción"), null=True, blank=True)
    target_audience = models.JSONField(
        _("Público Objetivo"), default=dict, blank=True, help_text=_("Descripción del público objetivo (JSON)")
    )
    budget = models.DecimalField(
        _("Presupuesto"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(
        _("Activa"), default=True, help_text=_("¿La campaña está activa actualmente?")
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = _("Campaña")
        verbose_name_plural = _("Campañas")

    def __str__(self):
        status = _("[ACTIVA]") if self.is_active else _("[INACTIVA]")
        return f"{self.campaign_name} ({self.campaign_code}) {status}"

class Service(models.Model):
    """Servicios ofrecidos por la agencia."""
    code = models.CharField(
        _("Código Servicio"), max_length=10, primary_key=True, help_text=_("Código único del servicio (ej. OD001)")
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.PROTECT, related_name='services',
        help_text=_("Categoría principal del servicio"), verbose_name=_("Categoría")
    )
    name = models.CharField(
        _("Nombre Servicio"), max_length=255, help_text=_("Nombre descriptivo del servicio")
    )
    is_active = models.BooleanField(
        _("Activo"), default=True, help_text=_("¿El servicio está activo y disponible para la venta?")
    )
    ventulab = models.BooleanField(
        _("Ventulab"), default=False, help_text=_("¿Es un servicio interno o especial de Ventulab?")
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promoted_services', help_text=_("Campaña promocional asociada directa (opcional)"),
        verbose_name=_("Campaña Asociada")
    )
    is_package = models.BooleanField(
        _("Es Paquete"), default=False, help_text=_("¿Este servicio es un paquete que agrupa otros?")
    )
    is_subscription = models.BooleanField(
        _("Es Suscripción"), default=False, help_text=_("¿Este servicio es una suscripción recurrente?")
    )
    audience = models.TextField(
        _("Público Objetivo"), blank=True, null=True, help_text=_("Público objetivo principal de este servicio")
    )
    detailed_description = models.TextField(
        _("Descripción Detallada"), blank=True, null=True, help_text=_("Descripción más detallada del servicio")
    )
    problem_solved = models.TextField(
        _("Problema que Soluciona"), blank=True, null=True, help_text=_("Qué problema o necesidad soluciona este servicio")
    )

    class Meta:
        ordering = ['category', 'name']
        verbose_name = _("Servicio")
        verbose_name_plural = _("Servicios")

    def __str__(self):
        package_indicator = _(" [Paquete]") if self.is_package else ""
        subscription_indicator = _(" [Suscripción]") if self.is_subscription else ""
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        return f"{self.name} ({self.code}){package_indicator}{subscription_indicator} {status}"

    def get_current_price(self, currency='EUR'):
        """Obtiene el precio más reciente para una moneda específica."""
        latest_price = self.price_history.filter(currency=currency).order_by('-effective_date').first()
        return latest_price.amount if latest_price else None

class ServiceFeature(models.Model):
    """Características, beneficios o detalles de un servicio."""
    FEATURE_TYPES = [
        ('differentiator', _('Diferenciador')), ('benefit', _('Beneficio')),
        ('caracteristicas', _('Características')), ('process', _('Proceso')),
        ('result', _('Resultado Esperado')),
    ]
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='features', verbose_name=_("Servicio")
    )
    feature_type = models.CharField(
        _("Tipo"), max_length=20, choices=FEATURE_TYPES, help_text=_("Tipo de característica")
    )
    description = models.TextField(
        _("Descripción"), help_text=_("Descripción de la característica, beneficio, etc.")
    )

    class Meta:
        ordering = ['service', 'feature_type']
        verbose_name = _("Característica de Servicio")
        verbose_name_plural = _("Características de Servicios")

    def __str__(self):
        service_code = self.service.code if hasattr(self, 'service') else 'N/A'
        return f"{service_code} - {self.get_feature_type_display()}: {self.description[:50]}..."

class Price(models.Model):
    """Historial de precios para un servicio."""
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='price_history', verbose_name=_("Servicio")
    )
    amount = models.DecimalField(_("Monto"), max_digits=12, decimal_places=2)
    currency = models.CharField(
        _("Moneda"), max_length=3, default='EUR', help_text=_("Código ISO 4217 (ej. EUR, USD, CLP, COP)")
    )
    effective_date = models.DateField(
        _("Fecha Efectiva"), default=datetime.date.today, help_text=_("Fecha desde la que este precio es válido")
    )

    class Meta:
        get_latest_by = 'effective_date'
        ordering = ['service', 'currency', '-effective_date']
        unique_together = ['service', 'currency', 'effective_date']
        verbose_name = _("Precio Histórico")
        verbose_name_plural = _("Historial de Precios")

    def __str__(self):
        service_code = self.service.code if hasattr(self, 'service') else 'N/A'
        return f"{_('Precio')} de {service_code} - {self.amount} {self.currency} ({_('desde')} {self.effective_date})"

class OrderService(models.Model):
    """Servicio específico incluido en un pedido."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='services', verbose_name=_("Pedido"))
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='order_lines', verbose_name=_("Servicio"))
    quantity = models.PositiveIntegerField(_("Cantidad"), default=1)
    price = models.DecimalField(
        _("Precio Unitario"), max_digits=12, decimal_places=2,
        help_text=_("Precio unitario en el momento de añadir a la orden")
    )
    note = models.TextField(_("Nota"), blank=True, help_text=_("Notas específicas para este servicio en esta orden"))

    class Meta:
        verbose_name = _("Servicio del Pedido")
        verbose_name_plural = _("Servicios del Pedido")
        ordering = ['order', 'id']

    def __str__(self):
        service_name = self.service.name if hasattr(self, 'service') else 'N/A'
        order_id = self.order_id if hasattr(self, 'order_id') else 'N/A'
        return f"{_('Servicio')} '{service_name}' x{self.quantity} en {_('Pedido')} #{order_id}"

    def save(self, *args, **kwargs):
        # Asignar precio base si es nuevo y no tiene precio
        if not self.pk and (self.price is None or self.price <= Decimal('0.00')):
            base_price = None
            try:
                 if self.service_id:
                      service_instance = Service.objects.get(pk=self.service_id)
                      base_price = service_instance.get_current_price(currency='EUR')
            except Service.DoesNotExist: logger.warning(f"Servicio ID {self.service_id} no encontrado al guardar OrderService.")
            except Exception as e: logger.error(f"Error obteniendo precio base para servicio ID {self.service_id}: {e}")
            self.price = base_price if base_price is not None else Decimal('0.00')
        super().save(*args, **kwargs) # Llamar al save original

class Deliverable(models.Model):
    """Entregable o tarea asociada a un pedido."""
    STATUS_CHOICES = [
        ('PENDING', _('Pendiente')), ('ASSIGNED', _('Asignado')), ('IN_PROGRESS', _('En Progreso')),
        ('PENDING_APPROVAL', _('Pendiente Aprobación Cliente')), ('PENDING_INTERNAL_APPROVAL', _('Pendiente Aprobación Interna')),
        ('REQUIRES_INFO', _('Requiere Info Adicional')), ('REVISION_REQUESTED', _('Revisión Solicitada')),
        ('APPROVED', _('Aprobado')), ('COMPLETED', _('Completado')), ('REJECTED', _('Rechazado')),
    ]
    FINAL_STATUSES = ['COMPLETED', 'REJECTED']

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliverables', verbose_name=_("Pedido"))
    file = models.FileField(_("Archivo"), upload_to='deliverables/%Y/%m/', null=True, blank=True, help_text=_("Archivo entregable (opcional inicialmente)"))
    description = models.TextField(_("Descripción"), help_text=_("Descripción clara de la tarea o entregable"))
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    version = models.PositiveIntegerField(_("Versión"), default=1)
    status = models.CharField(_("Estado"), max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    due_date = models.DateField(_("Fecha Límite"), null=True, blank=True, help_text=_("Fecha límite para este entregable"))
    assigned_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliverables', verbose_name=_("Empleado Asignado"))
    assigned_provider = models.ForeignKey('Provider', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliverables', verbose_name=_("Proveedor Asignado"))
    feedback_notes = models.TextField(_("Notas de Feedback"), blank=True, help_text=_("Comentarios o feedback recibido"))

    class Meta:
        ordering = ['order', 'due_date', 'created_at']
        verbose_name = _("Entregable/Tarea")
        verbose_name_plural = _("Entregables/Tareas")

    def __str__(self):
        due = f" ({_('Vence')}: {self.due_date})" if self.due_date else ""
        order_id = self.order_id if hasattr(self, 'order_id') else 'N/A'
        status_display = self.get_status_display()
        desc_short = (self.description[:27] + '...') if len(self.description) > 30 else self.description
        return f"{_('Entregable')} '{desc_short}' ({status_display}){due} - {_('Pedido')} #{order_id}"

class TransactionType(models.Model):
    """Tipos de transacciones financieras."""
    name = models.CharField(
        _("Nombre Tipo Transacción"), max_length=50, unique=True,
        help_text=_("Ej: Pago Cliente, Reembolso, Gasto Proveedor")
    )
    requires_approval = models.BooleanField(_("Requiere Aprobación"), default=False)

    class Meta:
        verbose_name = _("Tipo de Transacción")
        verbose_name_plural = _("Tipos de Transacciones")
        ordering = ['name']

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    """Métodos de pago aceptados."""
    name = models.CharField(
        _("Nombre Método Pago"), max_length=50, unique=True,
        help_text=_("Ej: Transferencia, Tarjeta, PayPal")
    )
    is_active = models.BooleanField(_("Activo"), default=True)

    class Meta:
        verbose_name = _("Método de Pago")
        verbose_name_plural = _("Métodos de Pago")
        ordering = ['name']

    def __str__(self):
        return f"{self.name}{'' if self.is_active else _(' (Inactivo)')}"

class Invoice(models.Model):
    """Facturas emitidas a clientes."""
    STATUS_CHOICES = [
        ('DRAFT', _('Borrador')), ('SENT', _('Enviada')), ('PAID', _('Pagada')),
        ('PARTIALLY_PAID', _('Parcialmente Pagada')), ('OVERDUE', _('Vencida')),
        ('CANCELLED', _('Cancelada')), ('VOID', _('Anulada Post-Pago')),
    ]
    FINAL_STATUSES = ['PAID', 'CANCELLED', 'VOID']

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name='invoices',
        help_text=_("Pedido al que corresponde la factura"), verbose_name=_("Pedido")
    )
    invoice_number = models.CharField(
        _("Número Factura"), max_length=50, unique=True, blank=True,
        help_text=_("Número de factura (puede autogenerarse)")
    )
    date = models.DateField(_("Fecha Emisión"), default=datetime.date.today, help_text=_("Fecha de emisión de la factura"))
    due_date = models.DateField(_("Fecha Vencimiento"), help_text=_("Fecha de vencimiento del pago"))
    paid_amount = models.DecimalField(
        _("Monto Pagado"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False
    )
    status = models.CharField(
        _("Estado"), max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    notes = models.TextField(_("Notas/Términos"), blank=True, help_text=_("Notas o términos de la factura"))

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = _("Factura")
        verbose_name_plural = _("Facturas")

    @property
    def total_amount(self):
        return self.order.total_amount if hasattr(self, 'order') and self.order else Decimal('0.00')
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    def update_paid_amount_and_status(self, trigger_notifications=True):
        """Actualiza montos y estado según pagos. Llama a create_notification si vence."""
        original_status = self.status
        # Usar try-except por si payments no está disponible aún (raro)
        try: total_paid = self.payments.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        except Exception: total_paid = Decimal('0.00')
        new_status = self.status; current_total = self.total_amount
        if self.status not in self.FINAL_STATUSES + ['DRAFT']: # No cambiar estados finales o borrador automáticamente
            if total_paid >= current_total and current_total > 0: new_status = 'PAID'
            elif total_paid > 0: new_status = 'PARTIALLY_PAID'
            elif self.due_date and self.due_date < timezone.now().date(): new_status = 'OVERDUE'
            elif self.status == 'OVERDUE' and self.due_date and self.due_date >= timezone.now().date(): new_status = 'SENT' # Volver a SENT si ya no está vencida
            else: new_status = 'SENT' # Estado por defecto si no es final/borrador/pagada/vencida
        status_changed = (new_status != self.status); paid_amount_changed = (total_paid != self.paid_amount)
        if (status_changed or paid_amount_changed) and self.pk:
             Invoice.objects.filter(pk=self.pk).update(paid_amount=total_paid, status=new_status)
             self.paid_amount = total_paid; self.status = new_status # Actualizar instancia
             if trigger_notifications and status_changed and self.status == 'OVERDUE' and hasattr(self, 'order') and self.order.customer:
                 message = f"Recordatorio: La factura {self.invoice_number} para el pedido #{self.order_id} ha vencido."
                 # Llamar a la función global definida más abajo
                 create_notification(self.order.customer.user, message, self)

    def save(self, *args, **kwargs):
        # Autogenerar número de factura
        if not self.pk and not self.invoice_number:
            last_invoice = Invoice.objects.order_by('id').last(); next_id = (last_invoice.id + 1) if last_invoice else 1
            current_year = datetime.date.today().year; self.invoice_number = f"INV-{current_year}-{next_id:04d}"
            while Invoice.objects.filter(invoice_number=self.invoice_number).exists(): next_id +=1; self.invoice_number = f"INV-{current_year}-{next_id:04d}"
        super().save(*args, **kwargs) # Guardar primero

    def __str__(self):
        customer_str = str(self.order.customer) if hasattr(self, 'order') and self.order else 'N/A'
        return f"{_('Factura')} {self.invoice_number} ({self.get_status_display()}) - {customer_str}"

class Payment(models.Model):
    """Registro de un pago asociado a una factura."""
    STATUS_CHOICES = [ ('PENDING', _('Pendiente')), ('COMPLETED', _('Completado')), ('FAILED', _('Fallido')), ('REFUNDED', _('Reembolsado')), ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name=_("Factura"))
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, help_text=_("Método utilizado para el pago"), verbose_name=_("Método de Pago"))
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT, help_text=_("Tipo de transacción (ej. pago, reembolso)"), verbose_name=_("Tipo Transacción"))
    date = models.DateTimeField(_("Fecha Pago"), default=timezone.now, help_text=_("Fecha y hora en que se registró el pago"))
    amount = models.DecimalField(_("Monto"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Moneda"), max_length=3, default='EUR')
    status = models.CharField(_("Estado"), max_length=20, choices=STATUS_CHOICES, default='COMPLETED', db_index=True)
    transaction_id = models.CharField(_("ID Transacción Externa"), max_length=100, blank=True, null=True, help_text=_("ID de la transacción externa si aplica"))
    notes = models.TextField(_("Notas"), blank=True, help_text=_("Notas sobre el pago"))

    class Meta:
        ordering = ['-date']
        verbose_name = _("Pago")
        verbose_name_plural = _("Pagos")

    def __str__(self):
        invoice_num = self.invoice.invoice_number if hasattr(self, 'invoice') else 'N/A'
        return f"{_('Pago')} ({self.get_status_display()}) de {self.amount} {self.currency} para {_('Factura')} {invoice_num}"

class CampaignService(models.Model):
    """Relación entre una campaña y un servicio incluido."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='included_services', verbose_name=_("Campaña"))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='campaign_assignments', verbose_name=_("Servicio"))
    discount_percentage = models.DecimalField(_("Descuento (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text=_("Descuento aplicado a este servicio en la campaña (%)"))
    additional_details = models.TextField(_("Detalles Adicionales"), null=True, blank=True)

    class Meta:
        unique_together = ('campaign', 'service')
        verbose_name = _("Servicio de Campaña")
        verbose_name_plural = _("Servicios de Campañas")

    def __str__(self):
        discount_str = f" ({self.discount_percentage}%)" if self.discount_percentage > 0 else ""
        service_name = self.service.name if hasattr(self, 'service') else 'N/A'
        campaign_name = self.campaign.campaign_name if hasattr(self, 'campaign') else 'N/A'
        return f"{_('Servicio')} {service_name} en {_('Campaña')} {campaign_name}{discount_str}"

class Provider(models.Model):
    """Proveedores o colaboradores externos."""
    name = models.CharField(_("Nombre Proveedor"), max_length=255, unique=True)
    contact_person = models.CharField(_("Persona de Contacto"), max_length=255, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True)
    phone = models.CharField(_("Teléfono"), max_length=30, null=True, blank=True)
    services_provided = models.ManyToManyField(
        Service, blank=True, related_name='providers',
        help_text=_("Servicios que ofrece este proveedor"), verbose_name=_("Servicios Ofrecidos")
    )
    rating = models.DecimalField(
        _("Calificación"), max_digits=3, decimal_places=1, default=Decimal('5.0'),
        help_text=_("Calificación interna (1-5)")
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    notes = models.TextField(_("Notas Internas"), blank=True, help_text=_("Notas internas sobre el proveedor"))

    class Meta:
        verbose_name = _("Proveedor")
        verbose_name_plural = _("Proveedores")
        ordering = ['name']

    def __str__(self):
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        return f"{self.name} {status}"

class Notification(models.Model):
    """Notificaciones para usuarios."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("Usuario"))
    message = models.TextField(_("Mensaje"))
    read = models.BooleanField(_("Leída"), default=False, db_index=True)
    created_at = models.DateTimeField(_("Fecha Creación"), auto_now_add=True)
    link = models.URLField(_("Enlace"), null=True, blank=True, help_text=_("Enlace relevante (ej. a un pedido, tarea)"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notificación")
        verbose_name_plural = _("Notificaciones")

    def __str__(self):
        status = _("[Leída]") if self.read else _("[No Leída]")
        username = self.user.username if hasattr(self, 'user') else 'N/A'
        return f"{_('Notificación')} para {username} {status}: {self.message[:50]}..."

class AuditLog(models.Model):
    """Registro de auditoría de acciones importantes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs', verbose_name=_("Usuario")
    )
    action = models.CharField(
        _("Acción"), max_length=255, help_text=_("Descripción de la acción realizada")
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    details = models.JSONField(
        _("Detalles"), default=dict, blank=True, help_text=_("Detalles adicionales en formato JSON")
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Registro de Auditoría")
        verbose_name_plural = _("Registros de Auditoría")

    def __str__(self):
        user_str = self.user.username if self.user else _("Sistema")
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else 'N/A'
        return f"{timestamp_str} - {user_str}: {self.action}"

# ==============================================================================
# ---------------------- MÉTODOS AÑADIDOS AL MODELO USER ----------------------
# ==============================================================================

UserModel = get_user_model()

# --- Propiedades y Métodos para Roles (Con Caché) ---
@property
def primary_role(self):
    cache_key = '_primary_role_cache'
    if not hasattr(self, cache_key):
        role = None
        try:
            profile = getattr(self, 'profile', None)
            if profile and profile.primary_role and profile.primary_role.is_active:
                role = profile.primary_role
        except Exception: pass # Captura genérica por si profile no es UserProfile
        setattr(self, cache_key, role)
    return getattr(self, cache_key)

@property
def primary_role_name(self):
    role = self.primary_role; return role.name if role else None

@property
def get_secondary_active_roles(self):
    cache_key = '_secondary_roles_cache'
    if not hasattr(self, cache_key):
        primary_role_id = None
        try: primary_role_id = self.profile.primary_role_id
        except Exception: pass
        qs = UserRole.objects.none()
        if self.pk:
             qs = UserRole.objects.filter(secondary_assignments__user_id=self.pk, secondary_assignments__is_active=True, is_active=True).distinct()
             if primary_role_id: qs = qs.exclude(id=primary_role_id)
        setattr(self, cache_key, qs)
    return getattr(self, cache_key)

@property
def get_secondary_active_role_names(self):
    return list(self.get_secondary_active_roles.values_list('name', flat=True))

@property
def get_all_active_role_names(self):
    all_roles = set(self.get_secondary_active_role_names)
    p_role_name = self.primary_role_name
    if p_role_name: all_roles.add(p_role_name)
    return list(all_roles)

def has_role(self, role_name):
    if not role_name: return False
    if self.primary_role_name == role_name: return True
    return role_name in self.get_secondary_active_role_names

def is_dragon(self):
    # Asegurarse que Roles.DRAGON existe antes de llamar a has_role
    dragon_role_name = getattr(Roles, 'DRAGON', None)
    return self.has_role(dragon_role_name) if dragon_role_name else False

UserModel.add_to_class("primary_role", primary_role)
UserModel.add_to_class("primary_role_name", primary_role_name)
UserModel.add_to_class("get_secondary_active_roles", get_secondary_active_roles)
UserModel.add_to_class("get_secondary_active_role_names", get_secondary_active_role_names)
UserModel.add_to_class("get_all_active_role_names", get_all_active_role_names)
UserModel.add_to_class("has_role", has_role)
UserModel.add_to_class("is_dragon", is_dragon)


# ==============================================================================
# ---------------------- SEÑALES DE LA APLICACIÓN -----------------------------
# ==============================================================================

# --- Señal para crear UserProfile ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_signal(sender, instance, created, **kwargs):
    if created: UserProfile.objects.get_or_create(user=instance)

# --- Señal para crear Customer/Employee ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_or_employee_profile_signal(sender, instance, created, **kwargs):
    if created:
        has_employee = Employee.objects.filter(user=instance).exists()
        has_customer = Customer.objects.filter(user=instance).exists()
        if not has_employee and not has_customer:
            if instance.is_staff: Employee.objects.get_or_create(user=instance)
            else: Customer.objects.get_or_create(user=instance)

# --- Señales de Pedidos ---
@receiver(post_save, sender=OrderService)
@receiver(post_delete, sender=OrderService)
def update_order_total_on_service_change_signal(sender, instance, **kwargs):
    if instance.order_id:
        try:
            order = Order.objects.get(pk=instance.order_id)
            order.update_total_amount()
        except Order.DoesNotExist: logger.warning(f"Order {instance.order_id} no encontrada al actualizar total desde OrderService {instance.id}. Posiblemente eliminada.")
        except Exception as e: logger.error(f"Error inesperado actualizando total de Order {instance.order_id} desde OrderService {instance.id}: {e}")

@receiver(pre_save, sender=Order)
def set_order_completion_date_signal(sender, instance, **kwargs):
    original_instance = None
    if instance.pk:
        try: original_instance = Order.objects.get(pk=instance.pk)
        except Order.DoesNotExist: pass
    if not instance.pk or original_instance:
        original_status = original_instance.status if original_instance else None
        if instance.status == 'DELIVERED' and original_status != 'DELIVERED': instance.completed_at = timezone.now()
        elif instance.status != 'DELIVERED' and (original_status == 'DELIVERED' or (not instance.pk and instance.status != 'DELIVERED')): instance.completed_at = None # Limpiar si ya no está entregado
        # elif not instance.pk and instance.status == 'DELIVERED': instance.completed_at = timezone.now() # Cubierto por primer if si status es DELIVERED

# --- Señales de Pagos y Facturas ---
@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def update_invoice_status_on_payment_signal(sender, instance, **kwargs):
    if instance.invoice_id:
        try:
            invoice = Invoice.objects.select_related('order__customer__user').get(pk=instance.invoice_id) # Optimizar
            invoice.update_paid_amount_and_status()
        except Invoice.DoesNotExist: logger.warning(f"Invoice {instance.invoice_id} no encontrada al actualizar estado desde Payment {instance.id}. Posiblemente eliminada.")
        except Exception as e: logger.error(f"Error inesperado actualizando estado de Invoice {instance.invoice_id} desde Payment {instance.id}: {e}")

# --- Helper Función Global para Notificaciones ---
def create_notification(user_recipient, message, link_obj=None):
    UserModelForCheck = get_user_model()
    if not user_recipient or not isinstance(user_recipient, UserModelForCheck): return
    link_url = None
    if link_obj and hasattr(link_obj, 'pk') and link_obj.pk:
        try:
            model_name = link_obj.__class__.__name__.lower(); app_label = link_obj._meta.app_label
            link_url = reverse(f'admin:{app_label}_{model_name}_change', args=[link_obj.pk])
        except Exception: pass # Silenciar error si URL no se puede generar
    try: Notification.objects.create(user=user_recipient, message=message, link=link_url)
    except Exception as e: logger.error(f"Error al crear notificación para {user_recipient.username}: {e}")

# --- Señales de Auditoría ---
def log_action(instance, action_verb, details_dict=None):
    user = get_current_user(); model_name = instance.__class__.__name__
    try: instance_str = str(instance)
    except Exception: instance_str = f"ID {instance.pk}" if instance.pk else "objeto no guardado/eliminado"
    action_str = f"{model_name} {action_verb}: {instance_str}"
    log_details = {'model': model_name, 'pk': instance.pk if instance.pk else None, 'representation': instance_str}
    if details_dict: log_details.update(details_dict)
    try: AuditLog.objects.create(user=user, action=action_str, details=log_details)
    except Exception as e: logger.error(f"Error al crear AuditLog: {e}")

AUDITED_MODELS = [Order, Invoice, Deliverable, Customer, Employee, Service, Payment, Provider, Campaign, UserProfile, UserRoleAssignment]

@receiver(post_save)
def audit_log_save_signal(sender, instance, created, **kwargs):
    if sender in AUDITED_MODELS:
        action_verb = "Creado" if created else "Actualizado"; details = {}
        if hasattr(instance, 'status'): status_val = getattr(instance, 'status', None); display_method = getattr(instance, 'get_status_display', None); details['status'] = display_method() if callable(display_method) else status_val
        if isinstance(instance, UserProfile) and instance.primary_role: details['primary_role'] = instance.primary_role.name
        if isinstance(instance, UserRoleAssignment) and instance.role: details['role'] = instance.role.name; details['assignment_active'] = instance.is_active
        log_action(instance, action_verb, details)

@receiver(post_delete)
def audit_log_delete_signal(sender, instance, **kwargs):
    if sender in AUDITED_MODELS: log_action(instance, "Eliminado")

# --- Señales de Notificación ---
@receiver(post_save, sender=Deliverable)
def notify_deliverable_signal(sender, instance, created, **kwargs):
    original_instance = None; assigned_employee_changed = False; status_changed = False
    current_assigned_employee_id = instance.assigned_employee_id # Cachear ID actual

    if not created and instance.pk:
        try: original_instance = Deliverable.objects.select_related('assigned_employee').get(pk=instance.pk)
        except Deliverable.DoesNotExist: pass

    if original_instance:
         if current_assigned_employee_id != original_instance.assigned_employee_id: assigned_employee_changed = True
         original_status = original_instance.status
         if original_status != instance.status: status_changed = True
    elif created: # Si es nuevo
        if current_assigned_employee_id: assigned_employee_changed = True # Se asignó al crear
        status_changed = True # El status siempre cambia de 'nada' a 'PENDING' (o lo que sea)
    else: original_status = None; status_changed = True # Caso raro: sin pk pero no creado

    # Notificar nueva asignación
    if assigned_employee_changed and instance.assigned_employee:
        if hasattr(instance.assigned_employee, 'user') and instance.assigned_employee.user:
            message = f"Te han asignado la tarea '{instance.description[:50]}...' del Pedido #{instance.order_id}"
            create_notification(instance.assigned_employee.user, message, instance)
        else: logger.warning(f"Empleado asignado ID {current_assigned_employee_id} a Deliverable {instance.id} no tiene usuario.")

    # Notificar cambio de estado relevante
    if status_changed:
        recipient, message = None, None
        try:
            # Solo notificar cambios de estado específicos, no todos
            notify_states = ['PENDING_APPROVAL', 'REVISION_REQUESTED', 'REQUIRES_INFO', 'APPROVED', 'COMPLETED'] # Estados que podrían generar notificación
            if instance.status in notify_states:
                if instance.status == 'PENDING_APPROVAL' and instance.order.customer:
                     recipient = instance.order.customer.user
                     message = f"La tarea '{instance.description[:50]}...' del Pedido #{instance.order_id} está lista para tu aprobación."
                elif instance.status in ['REVISION_REQUESTED', 'REQUIRES_INFO'] and instance.assigned_employee and hasattr(instance.assigned_employee, 'user'):
                     recipient = instance.assigned_employee.user
                     message = f"La tarea '{instance.description[:50]}...' (Pedido #{instance.order_id}) requiere tu atención: {instance.get_status_display()}."
                elif instance.status == 'APPROVED' and instance.assigned_employee and hasattr(instance.assigned_employee, 'user'):
                      recipient = instance.assigned_employee.user # Notificar al empleado que se aprobó? O al cliente?
                      message = f"La tarea '{instance.description[:50]}...' (Pedido #{instance.order_id}) ha sido aprobada."
                # Añadir más lógica según necesites
            if recipient and message: create_notification(recipient, message, instance)
        except Order.DoesNotExist: logger.warning(f"Orden {instance.order_id} no encontrada al notificar sobre Deliverable {instance.id}")
        except Exception as e: logger.error(f"Error procesando notificación para Deliverable {instance.id}: {e}")

===== permissions.py =====

# api/permissions.py
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions # <--- ¡IMPORTACIÓN AÑADIDA!

# Importar constantes de roles
try:
    from .roles import Roles
except ImportError:
    class Roles:
        DRAGON = 'dragon'; ADMIN = 'admin'; MARKETING = 'mktg'; FINANCE = 'fin';
        SALES = 'sales'; DEVELOPMENT = 'dev'; SUPPORT = 'support'; OPERATIONS = 'ops';
        DESIGN = 'design'; AUDIOVISUAL = 'av';
    print("ADVERTENCIA: api/roles.py no encontrado. Usando roles placeholder.")

# Importar modelos si son necesarios
# from .models import Order, Customer

# ==============================================================================
# ------------------------- PERMISOS PERSONALIZADOS --------------------------
# ==============================================================================

class HasRolePermission(BasePermission):
    required_roles = []
    message = _("No tienes permiso para realizar esta acción debido a tu rol.")

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_has_required_role = False
        if hasattr(request.user, 'has_role'):
            user_has_required_role = any(request.user.has_role(role) for role in self.required_roles)
        elif hasattr(request.user, 'get_all_active_role_names'):
             try:
                 user_roles = set(request.user.get_all_active_role_names)
                 user_has_required_role = any(role in user_roles for role in self.required_roles)
             except Exception:
                 pass
        return request.user.is_staff or user_has_required_role

# --- Subclases específicas ---
class CanAccessDashboard(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.FINANCE, Roles.MARKETING, Roles.SALES, Roles.OPERATIONS]
    message = _("No tienes permiso para acceder al dashboard.")

class IsAdminOrDragon(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON]
    message = _("Necesitas ser Administrador o Dragón para esta acción.")

class CanManageEmployees(IsAdminOrDragon):
    message = _("No tienes permiso para gestionar empleados.")

class CanManageJobPositions(IsAdminOrDragon):
     message = _("No tienes permiso para gestionar puestos de trabajo.")

class CanManageCampaigns(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.MARKETING]
    message = _("No tienes permiso para gestionar campañas.")

class CanManageServices(IsAdminOrDragon):
    message = _("No tienes permiso para gestionar servicios.")

class CanManageFinances(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.FINANCE]
    message = _("No tienes permiso para realizar operaciones financieras.")

class CanViewAllOrders(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES, Roles.SUPPORT, Roles.OPERATIONS]
    message = _("No tienes permiso para ver todos los pedidos.")

class CanCreateOrders(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES]
    message = _("No tienes permiso para crear pedidos.")

class CanViewAllDeliverables(IsAdminOrDragon):
     message = _("No tienes permiso para ver todos los entregables.")

class CanCreateDeliverables(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.DEVELOPMENT, Roles.DESIGN, Roles.AUDIOVISUAL, Roles.OPERATIONS]
    message = _("No tienes permiso para crear entregables.")

class CanViewFormResponses(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES, Roles.SUPPORT]
    message = _("No tienes permiso para ver las respuestas de formularios.")

class CanViewAuditLogs(IsAdminOrDragon):
    message = _("No tienes permiso para ver los registros de auditoría.")

# --- Permisos adicionales ---

class IsOwnerOrReadOnly(BasePermission):
    """
    Permiso a nivel de objeto para permitir solo a los propietarios de un objeto editarlo.
    Asume que el objeto tiene un atributo 'user' o 'customer.user'.
    """
    def has_object_permission(self, request, view, obj):
        # La corrección está aquí: se usa 'permissions.SAFE_METHODS' importado arriba
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        owner = getattr(obj, 'user', None) or getattr(getattr(obj, 'customer', None), 'user', None)
        return owner == request.user

class IsCustomerOwnerOrAdminOrSupport(BasePermission):
    message = _("No tienes permiso para acceder a este cliente.")

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'customer_profile') and obj == request.user.customer_profile:
            return True
        if hasattr(request.user, 'employee_profile'):
            required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SUPPORT, Roles.SALES]
            if hasattr(request.user, 'has_role'):
                 if any(request.user.has_role(role) for role in required_roles):
                     return True
            elif request.user.is_staff:
                 return True
        return False

===== roles.py =====

# api/roles.py
"""
Define constantes para los nombres internos de los roles de usuario.
Esto evita errores tipográficos y hace el código más legible.
"""

class Roles:
    # Core / Admin Roles
    DRAGON = 'dragon'        # Superusuario específico de la app con acceso total
    ADMIN = 'admin'          # Administrador general de la aplicación

    # Department / Function Roles (Primarios Típicos)
    MARKETING = 'mktg'       # Equipo de Marketing
    FINANCE = 'fin'          # Equipo de Finanzas
    SALES = 'sales'          # Equipo de Ventas
    DEVELOPMENT = 'dev'      # Equipo de Desarrollo
    AUDIOVISUAL = 'avps'     # Equipo de Producción Audiovisual
    DESIGN = 'dsgn'          # Equipo de Diseño
    SUPPORT = 'support'      # Equipo de Soporte al Cliente
    OPERATIONS = 'ops'       # Equipo de Operaciones Internas
    HR = 'hr'                # Recursos Humanos (Ejemplo adicional)

    # Podrías añadir roles secundarios/permisos aquí si los necesitas muy definidos
    # REPORT_VIEWER = 'report_viewer'
    # CONTENT_PUBLISHER = 'content_publisher'

    # Puedes añadir un método para obtener una lista o diccionario si es útil
    @classmethod
    def get_all_roles(cls):
        return [getattr(cls, attr) for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("__")]



===== models.py =====

# api/models.py

import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, DecimalField, DurationField, ExpressionWrapper, F, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

# --- Importa tus constantes de roles ---
try:
    from .roles import Roles
except ImportError:
    # Define placeholders si el archivo no existe (la app podría fallar si no existen realmente)
    class Roles:
        DRAGON = 'dragon'; ADMIN = 'admin'; MARKETING = 'mktg'; FINANCE = 'fin'
        SALES = 'sales'; DEVELOPMENT = 'dev'; AUDIOVISUAL = 'avps'; DESIGN = 'dsgn'
        SUPPORT = 'support'; OPERATIONS = 'ops'; HR = 'hr'
    print("ADVERTENCIA: api/roles.py no encontrado. Usando roles placeholder.")


# --- Helper para obtener usuario actual (requiere django-crum) ---
try:
    from crum import get_current_user
except ImportError:
    get_current_user = lambda: None
    print("ADVERTENCIA: django-crum no está instalado. Los AuditLogs no registrarán el usuario.")

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

# ==============================================================================
# ------ MODELOS DE GESTIÓN DE USUARIOS, ROLES Y PERFILES ---------------------
# ==============================================================================

class UserRole(models.Model):
    """Define los roles disponibles en la aplicación (Primarios y Secundarios)."""
    name = models.CharField(
        _("Internal Name"), max_length=50, unique=True,
        help_text=_("Short internal alias (e.g., 'dev', 'mktg'). Use constants from roles.py.")
    )
    display_name = models.CharField(
        _("Display Name"), max_length=100,
        help_text=_("User-friendly name shown in interfaces.")
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Role")
        verbose_name_plural = _("User Roles")
        ordering = ['display_name']

    def __str__(self):
        return self.display_name

class UserProfile(models.Model):
    """Extiende el modelo User para almacenar el rol principal obligatorio."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, primary_key=True, related_name='profile', verbose_name=_("User")
    )
    primary_role = models.ForeignKey(
        UserRole, on_delete=models.PROTECT, null=True, blank=False, # null=True temporal para señal
        related_name='primary_users', verbose_name=_("Primary Role"),
        help_text=_("The main mandatory role defining the user's core function.")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        role_name = self.primary_role.display_name if self.primary_role else _("No primary role assigned")
        username = self.user.get_username() if hasattr(self, 'user') else 'N/A'
        return f"{username} - Profile ({role_name})"

    def clean(self):
        if not self.primary_role_id:
            raise ValidationError({'primary_role': _('A primary role must be assigned.')})

class UserRoleAssignment(models.Model):
    """Vincula un Usuario con un Rol SECUNDARIO (Acceso) específico."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='secondary_role_assignments', verbose_name=_("User")
    )
    role = models.ForeignKey(
        UserRole, on_delete=models.CASCADE,
        related_name='secondary_assignments', verbose_name=_("Secondary Role/Access")
    )
    is_active = models.BooleanField(_("Assignment Active"), default=True)
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        unique_together = ('user', 'role')
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
                primary_role_id = UserProfile.objects.filter(user_id=self.user_id).values_list('primary_role_id', flat=True).first()
                if primary_role_id and primary_role_id == self.role_id:
                    raise ValidationError({'role': _('This role is already assigned as the primary role for this user.')})
            except Exception as e:
                 logger.warning(f"Excepción durante validación de UserRoleAssignment.clean: {e}")
                 pass

# ==============================================================================
# ---------------------- MODELOS DE LA APLICACIÓN -----------------------------
# ==============================================================================

class Form(models.Model):
    """Modelo para definir estructuras de formularios."""
    name = models.CharField(_("Nombre del Formulario"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True)
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("Formulario")
        verbose_name_plural = _("Formularios")
        ordering = ['name']

    def __str__(self):
        return self.name

class FormQuestion(models.Model):
    """Pregunta específica dentro de un formulario."""
    form = models.ForeignKey(
        Form, on_delete=models.CASCADE, related_name='questions', verbose_name=_("Formulario")
    )
    question_text = models.TextField(_("Texto de la Pregunta"))
    order = models.PositiveIntegerField(
        _("Orden"), default=0, help_text=_("Orden de aparición en el formulario")
    )
    required = models.BooleanField(_("Requerida"), default=True)

    class Meta:
        ordering = ['form', 'order']
        verbose_name = _("Pregunta de Formulario")
        verbose_name_plural = _("Preguntas de Formularios")

    def __str__(self):
        form_name = self.form.name if hasattr(self, 'form') else 'N/A'
        return f"{form_name} - P{self.order}: {self.question_text[:50]}..."

class FormResponse(models.Model):
    """Respuesta de un cliente a una pregunta de un formulario."""
    customer = models.ForeignKey(
        'Customer', on_delete=models.CASCADE, related_name='form_responses', verbose_name=_("Cliente")
    )
    form = models.ForeignKey(
        Form, on_delete=models.CASCADE, related_name='responses', verbose_name=_("Formulario")
    )
    question = models.ForeignKey(
        FormQuestion, on_delete=models.CASCADE, related_name='responses', verbose_name=_("Pregunta")
    )
    text = models.TextField(_("Respuesta"), help_text=_("Respuesta proporcionada por el cliente"))
    created_at = models.DateTimeField(_("Fecha de Respuesta"), auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'form', 'question')
        ordering = ['created_at']
        verbose_name = _("Respuesta de Formulario")
        verbose_name_plural = _("Respuestas de Formularios")

    def __str__(self):
        customer_str = str(self.customer) if hasattr(self, 'customer') else 'N/A'
        question_str = str(self.question) if hasattr(self, 'question') else 'N/A'
        return f"{_('Respuesta')} de {customer_str} a {question_str}"

class Customer(models.Model):
    """Perfil de un cliente."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile', verbose_name=_("Usuario")
    )
    phone = models.CharField(_("Teléfono"), max_length=30, null=True, blank=True)
    address = models.TextField(_("Dirección"), null=True, blank=True)
    date_of_birth = models.DateField(_("Fecha de Nacimiento"), null=True, blank=True)
    country = CountryField(
        _("País"), blank=True, null=True, help_text=_("País del cliente")
    )
    company_name = models.CharField(
        _("Nombre de Empresa"), max_length=150, blank=True, null=True, help_text=_("Nombre de la empresa (si aplica)")
    )
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    preferred_contact_method = models.CharField(
        _("Método Contacto Preferido"), max_length=20,
        choices=[('email', 'Email'), ('phone', 'Teléfono'), ('whatsapp', 'WhatsApp'), ('other', 'Otro')],
        null=True, blank=True
    )
    brand_guidelines = models.FileField(
        _("Guías de Marca"), upload_to='customers/brand_guidelines/', null=True, blank=True
    )

    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        display_name = self.company_name or self.user.get_full_name() or self.user.username
        email = self.user.email if hasattr(self, 'user') else 'N/A'
        return f"{display_name} ({email})"

class JobPosition(models.Model):
    """Puesto de trabajo dentro de la organización."""
    name = models.CharField(_("Nombre del Puesto"), max_length=50, unique=True)
    description = models.TextField(_("Descripción"), null=True, blank=True)
    permissions = models.JSONField(
        _("Permisos JSON"), default=dict, blank=True, help_text=_("Permisos específicos para este puesto (estructura JSON)")
    )

    class Meta:
        verbose_name = _("Puesto de Trabajo")
        verbose_name_plural = _("Puestos de Trabajo")
        ordering = ['name']

    def __str__(self):
        return self.name

class Employee(models.Model):
    """Perfil de un empleado."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile', verbose_name=_("Usuario")
    )
    hire_date = models.DateField(_("Fecha Contratación"), default=datetime.date.today)
    address = models.TextField(_("Dirección"), null=True, blank=True)
    salary = models.DecimalField(
        _("Salario"), max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    position = models.ForeignKey(
        JobPosition, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employees', verbose_name=_("Puesto")
    )

    class Meta:
        verbose_name = _("Empleado")
        verbose_name_plural = _("Empleados")
        ordering = ['user__first_name', 'user__last_name']

    @property
    def is_active(self):
        return self.user.is_active

    def __str__(self):
        position_name = self.position.name if self.position else _("Sin puesto")
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        display_name = self.user.get_full_name() or self.user.get_username()
        return f"{display_name} ({position_name}) {status}"

class Order(models.Model):
    """Modelo principal para los pedidos de los clientes."""
    STATUS_CHOICES = [
        ('DRAFT', _('Borrador')), ('CONFIRMED', _('Confirmado')), ('PLANNING', _('Planificación')),
        ('IN_PROGRESS', _('En Progreso')), ('QUALITY_CHECK', _('Control de Calidad')),
        ('PENDING_DELIVERY', _('Pendiente Entrega')), ('DELIVERED', _('Entregado')),
        ('CANCELLED', _('Cancelado')), ('ON_HOLD', _('En Espera')),
    ]
    FINAL_STATUSES = ['DELIVERED', 'CANCELLED']

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='orders',
        help_text=_("Cliente que realiza el pedido"), verbose_name=_("Cliente")
    )
    employee = models.ForeignKey(
        Employee, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='managed_orders', help_text=_("Empleado responsable principal"), verbose_name=_("Empleado Asignado")
    )
    date_received = models.DateTimeField(_("Fecha Recepción"), auto_now_add=True)
    date_required = models.DateTimeField(_("Fecha Requerida"), help_text=_("Fecha límite solicitada por el cliente"))
    status = models.CharField(
        _("Estado"), max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    payment_due_date = models.DateTimeField(
        _("Vencimiento Pago"), null=True, blank=True, help_text=_("Fecha límite para el pago (si aplica)")
    )
    note = models.TextField(_("Nota Interna"), null=True, blank=True)
    priority = models.PositiveIntegerField(
        _("Prioridad"), default=3, help_text=_("Prioridad (ej. 1=Alta, 5=Baja)")
    )
    completed_at = models.DateTimeField(
        _("Fecha Completado"), null=True, blank=True, editable=False, help_text=_("Fecha y hora de finalización (status='DELIVERED')")
    )
    total_amount = models.DecimalField(
        _("Monto Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'),
        editable=False, help_text=_("Calculado de OrderService. Actualizado automáticamente.")
    )

    class Meta:
        ordering = ['priority', '-date_received']
        verbose_name = _("Pedido")
        verbose_name_plural = _("Pedidos")

    def __str__(self):
        customer_str = str(self.customer) if hasattr(self, 'customer') else 'N/A'
        return f"{_('Pedido')} #{self.id} ({self.get_status_display()}) - {customer_str}"

    def update_total_amount(self):
        """Calcula y guarda el monto total basado en los servicios asociados."""
        # Se asume que self.services existe en este punto
        total = self.services.aggregate(total=Sum(F('price') * F('quantity')))['total']
        calculated_total = total if total is not None else Decimal('0.00')
        # Actualizar solo si el valor calculado es diferente y el objeto ya existe
        if self.pk and self.total_amount != calculated_total:
             Order.objects.filter(pk=self.pk).update(total_amount=calculated_total)
             self.total_amount = calculated_total # Actualizar instancia en memoria

class ServiceCategory(models.Model):
    """Categorías para agrupar servicios."""
    code = models.CharField(
        _("Código Categoría"), max_length=10, primary_key=True,
        help_text=_("Código corto de la categoría (ej. MKT, DEV)")
    )
    name = models.CharField(
        _("Nombre Categoría"), max_length=100, help_text=_("Nombre descriptivo de la categoría")
    )

    class Meta:
        verbose_name = _("Categoría de Servicio")
        verbose_name_plural = _("Categorías de Servicios")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Campaign(models.Model):
    """Campañas de marketing o promocionales."""
    campaign_code = models.CharField(_("Código Campaña"), max_length=20, primary_key=True)
    campaign_name = models.CharField(_("Nombre Campaña"), max_length=255)
    start_date = models.DateTimeField(_("Fecha Inicio"), help_text=_("Fecha y hora de inicio de la campaña"))
    end_date = models.DateTimeField(
        _("Fecha Fin"), null=True, blank=True, help_text=_("Fecha y hora de fin (opcional)")
    )
    description = models.TextField(_("Descripción"), null=True, blank=True)
    target_audience = models.JSONField(
        _("Público Objetivo"), default=dict, blank=True, help_text=_("Descripción del público objetivo (JSON)")
    )
    budget = models.DecimalField(
        _("Presupuesto"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(
        _("Activa"), default=True, help_text=_("¿La campaña está activa actualmente?")
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = _("Campaña")
        verbose_name_plural = _("Campañas")

    def __str__(self):
        status = _("[ACTIVA]") if self.is_active else _("[INACTIVA]")
        return f"{self.campaign_name} ({self.campaign_code}) {status}"

class Service(models.Model):
    """Servicios ofrecidos por la agencia."""
    code = models.CharField(
        _("Código Servicio"), max_length=10, primary_key=True, help_text=_("Código único del servicio (ej. OD001)")
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.PROTECT, related_name='services',
        help_text=_("Categoría principal del servicio"), verbose_name=_("Categoría")
    )
    name = models.CharField(
        _("Nombre Servicio"), max_length=255, help_text=_("Nombre descriptivo del servicio")
    )
    is_active = models.BooleanField(
        _("Activo"), default=True, help_text=_("¿El servicio está activo y disponible para la venta?")
    )
    ventulab = models.BooleanField(
        _("Ventulab"), default=False, help_text=_("¿Es un servicio interno o especial de Ventulab?")
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promoted_services', help_text=_("Campaña promocional asociada directa (opcional)"),
        verbose_name=_("Campaña Asociada")
    )
    is_package = models.BooleanField(
        _("Es Paquete"), default=False, help_text=_("¿Este servicio es un paquete que agrupa otros?")
    )
    is_subscription = models.BooleanField(
        _("Es Suscripción"), default=False, help_text=_("¿Este servicio es una suscripción recurrente?")
    )
    audience = models.TextField(
        _("Público Objetivo"), blank=True, null=True, help_text=_("Público objetivo principal de este servicio")
    )
    detailed_description = models.TextField(
        _("Descripción Detallada"), blank=True, null=True, help_text=_("Descripción más detallada del servicio")
    )
    problem_solved = models.TextField(
        _("Problema que Soluciona"), blank=True, null=True, help_text=_("Qué problema o necesidad soluciona este servicio")
    )

    class Meta:
        ordering = ['category', 'name']
        verbose_name = _("Servicio")
        verbose_name_plural = _("Servicios")

    def __str__(self):
        package_indicator = _(" [Paquete]") if self.is_package else ""
        subscription_indicator = _(" [Suscripción]") if self.is_subscription else ""
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        return f"{self.name} ({self.code}){package_indicator}{subscription_indicator} {status}"

    def get_current_price(self, currency='EUR'):
        """Obtiene el precio más reciente para una moneda específica."""
        latest_price = self.price_history.filter(currency=currency).order_by('-effective_date').first()
        return latest_price.amount if latest_price else None

class ServiceFeature(models.Model):
    """Características, beneficios o detalles de un servicio."""
    FEATURE_TYPES = [
        ('differentiator', _('Diferenciador')), ('benefit', _('Beneficio')),
        ('caracteristicas', _('Características')), ('process', _('Proceso')),
        ('result', _('Resultado Esperado')),
    ]
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='features', verbose_name=_("Servicio")
    )
    feature_type = models.CharField(
        _("Tipo"), max_length=20, choices=FEATURE_TYPES, help_text=_("Tipo de característica")
    )
    description = models.TextField(
        _("Descripción"), help_text=_("Descripción de la característica, beneficio, etc.")
    )

    class Meta:
        ordering = ['service', 'feature_type']
        verbose_name = _("Característica de Servicio")
        verbose_name_plural = _("Características de Servicios")

    def __str__(self):
        service_code = self.service.code if hasattr(self, 'service') else 'N/A'
        return f"{service_code} - {self.get_feature_type_display()}: {self.description[:50]}..."

class Price(models.Model):
    """Historial de precios para un servicio."""
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='price_history', verbose_name=_("Servicio")
    )
    amount = models.DecimalField(_("Monto"), max_digits=12, decimal_places=2)
    currency = models.CharField(
        _("Moneda"), max_length=3, default='EUR', help_text=_("Código ISO 4217 (ej. EUR, USD, CLP, COP)")
    )
    effective_date = models.DateField(
        _("Fecha Efectiva"), default=datetime.date.today, help_text=_("Fecha desde la que este precio es válido")
    )

    class Meta:
        get_latest_by = 'effective_date'
        ordering = ['service', 'currency', '-effective_date']
        unique_together = ['service', 'currency', 'effective_date']
        verbose_name = _("Precio Histórico")
        verbose_name_plural = _("Historial de Precios")

    def __str__(self):
        service_code = self.service.code if hasattr(self, 'service') else 'N/A'
        return f"{_('Precio')} de {service_code} - {self.amount} {self.currency} ({_('desde')} {self.effective_date})"

class OrderService(models.Model):
    """Servicio específico incluido en un pedido."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='services', verbose_name=_("Pedido"))
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='order_lines', verbose_name=_("Servicio"))
    quantity = models.PositiveIntegerField(_("Cantidad"), default=1)
    price = models.DecimalField(
        _("Precio Unitario"), max_digits=12, decimal_places=2,
        help_text=_("Precio unitario en el momento de añadir a la orden")
    )
    note = models.TextField(_("Nota"), blank=True, help_text=_("Notas específicas para este servicio en esta orden"))

    class Meta:
        verbose_name = _("Servicio del Pedido")
        verbose_name_plural = _("Servicios del Pedido")
        ordering = ['order', 'id']

    def __str__(self):
        service_name = self.service.name if hasattr(self, 'service') else 'N/A'
        order_id = self.order_id if hasattr(self, 'order_id') else 'N/A'
        return f"{_('Servicio')} '{service_name}' x{self.quantity} en {_('Pedido')} #{order_id}"

    def save(self, *args, **kwargs):
        # Asignar precio base si es nuevo y no tiene precio
        if not self.pk and (self.price is None or self.price <= Decimal('0.00')):
            base_price = None
            try:
                 if self.service_id:
                      service_instance = Service.objects.get(pk=self.service_id)
                      base_price = service_instance.get_current_price(currency='EUR')
            except Service.DoesNotExist: logger.warning(f"Servicio ID {self.service_id} no encontrado al guardar OrderService.")
            except Exception as e: logger.error(f"Error obteniendo precio base para servicio ID {self.service_id}: {e}")
            self.price = base_price if base_price is not None else Decimal('0.00')
        super().save(*args, **kwargs) # Llamar al save original

class Deliverable(models.Model):
    """Entregable o tarea asociada a un pedido."""
    STATUS_CHOICES = [
        ('PENDING', _('Pendiente')), ('ASSIGNED', _('Asignado')), ('IN_PROGRESS', _('En Progreso')),
        ('PENDING_APPROVAL', _('Pendiente Aprobación Cliente')), ('PENDING_INTERNAL_APPROVAL', _('Pendiente Aprobación Interna')),
        ('REQUIRES_INFO', _('Requiere Info Adicional')), ('REVISION_REQUESTED', _('Revisión Solicitada')),
        ('APPROVED', _('Aprobado')), ('COMPLETED', _('Completado')), ('REJECTED', _('Rechazado')),
    ]
    FINAL_STATUSES = ['COMPLETED', 'REJECTED']

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliverables', verbose_name=_("Pedido"))
    file = models.FileField(_("Archivo"), upload_to='deliverables/%Y/%m/', null=True, blank=True, help_text=_("Archivo entregable (opcional inicialmente)"))
    description = models.TextField(_("Descripción"), help_text=_("Descripción clara de la tarea o entregable"))
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    version = models.PositiveIntegerField(_("Versión"), default=1)
    status = models.CharField(_("Estado"), max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    due_date = models.DateField(_("Fecha Límite"), null=True, blank=True, help_text=_("Fecha límite para este entregable"))
    assigned_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliverables', verbose_name=_("Empleado Asignado"))
    assigned_provider = models.ForeignKey('Provider', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliverables', verbose_name=_("Proveedor Asignado"))
    feedback_notes = models.TextField(_("Notas de Feedback"), blank=True, help_text=_("Comentarios o feedback recibido"))

    class Meta:
        ordering = ['order', 'due_date', 'created_at']
        verbose_name = _("Entregable/Tarea")
        verbose_name_plural = _("Entregables/Tareas")

    def __str__(self):
        due = f" ({_('Vence')}: {self.due_date})" if self.due_date else ""
        order_id = self.order_id if hasattr(self, 'order_id') else 'N/A'
        status_display = self.get_status_display()
        desc_short = (self.description[:27] + '...') if len(self.description) > 30 else self.description
        return f"{_('Entregable')} '{desc_short}' ({status_display}){due} - {_('Pedido')} #{order_id}"

class TransactionType(models.Model):
    """Tipos de transacciones financieras."""
    name = models.CharField(
        _("Nombre Tipo Transacción"), max_length=50, unique=True,
        help_text=_("Ej: Pago Cliente, Reembolso, Gasto Proveedor")
    )
    requires_approval = models.BooleanField(_("Requiere Aprobación"), default=False)

    class Meta:
        verbose_name = _("Tipo de Transacción")
        verbose_name_plural = _("Tipos de Transacciones")
        ordering = ['name']

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    """Métodos de pago aceptados."""
    name = models.CharField(
        _("Nombre Método Pago"), max_length=50, unique=True,
        help_text=_("Ej: Transferencia, Tarjeta, PayPal")
    )
    is_active = models.BooleanField(_("Activo"), default=True)

    class Meta:
        verbose_name = _("Método de Pago")
        verbose_name_plural = _("Métodos de Pago")
        ordering = ['name']

    def __str__(self):
        return f"{self.name}{'' if self.is_active else _(' (Inactivo)')}"

class Invoice(models.Model):
    """Facturas emitidas a clientes."""
    STATUS_CHOICES = [
        ('DRAFT', _('Borrador')), ('SENT', _('Enviada')), ('PAID', _('Pagada')),
        ('PARTIALLY_PAID', _('Parcialmente Pagada')), ('OVERDUE', _('Vencida')),
        ('CANCELLED', _('Cancelada')), ('VOID', _('Anulada Post-Pago')),
    ]
    FINAL_STATUSES = ['PAID', 'CANCELLED', 'VOID']

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name='invoices',
        help_text=_("Pedido al que corresponde la factura"), verbose_name=_("Pedido")
    )
    invoice_number = models.CharField(
        _("Número Factura"), max_length=50, unique=True, blank=True,
        help_text=_("Número de factura (puede autogenerarse)")
    )
    date = models.DateField(_("Fecha Emisión"), default=datetime.date.today, help_text=_("Fecha de emisión de la factura"))
    due_date = models.DateField(_("Fecha Vencimiento"), help_text=_("Fecha de vencimiento del pago"))
    paid_amount = models.DecimalField(
        _("Monto Pagado"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False
    )
    status = models.CharField(
        _("Estado"), max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    notes = models.TextField(_("Notas/Términos"), blank=True, help_text=_("Notas o términos de la factura"))

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = _("Factura")
        verbose_name_plural = _("Facturas")

    @property
    def total_amount(self):
        return self.order.total_amount if hasattr(self, 'order') and self.order else Decimal('0.00')
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    def update_paid_amount_and_status(self, trigger_notifications=True):
        """Actualiza montos y estado según pagos. Llama a create_notification si vence."""
        original_status = self.status
        # Usar try-except por si payments no está disponible aún (raro)
        try: total_paid = self.payments.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        except Exception: total_paid = Decimal('0.00')
        new_status = self.status; current_total = self.total_amount
        if self.status not in self.FINAL_STATUSES + ['DRAFT']: # No cambiar estados finales o borrador automáticamente
            if total_paid >= current_total and current_total > 0: new_status = 'PAID'
            elif total_paid > 0: new_status = 'PARTIALLY_PAID'
            elif self.due_date and self.due_date < timezone.now().date(): new_status = 'OVERDUE'
            elif self.status == 'OVERDUE' and self.due_date and self.due_date >= timezone.now().date(): new_status = 'SENT' # Volver a SENT si ya no está vencida
            else: new_status = 'SENT' # Estado por defecto si no es final/borrador/pagada/vencida
        status_changed = (new_status != self.status); paid_amount_changed = (total_paid != self.paid_amount)
        if (status_changed or paid_amount_changed) and self.pk:
             Invoice.objects.filter(pk=self.pk).update(paid_amount=total_paid, status=new_status)
             self.paid_amount = total_paid; self.status = new_status # Actualizar instancia
             if trigger_notifications and status_changed and self.status == 'OVERDUE' and hasattr(self, 'order') and self.order.customer:
                 message = f"Recordatorio: La factura {self.invoice_number} para el pedido #{self.order_id} ha vencido."
                 # Llamar a la función global definida más abajo
                 create_notification(self.order.customer.user, message, self)

    def save(self, *args, **kwargs):
        # Autogenerar número de factura
        if not self.pk and not self.invoice_number:
            last_invoice = Invoice.objects.order_by('id').last(); next_id = (last_invoice.id + 1) if last_invoice else 1
            current_year = datetime.date.today().year; self.invoice_number = f"INV-{current_year}-{next_id:04d}"
            while Invoice.objects.filter(invoice_number=self.invoice_number).exists(): next_id +=1; self.invoice_number = f"INV-{current_year}-{next_id:04d}"
        super().save(*args, **kwargs) # Guardar primero

    def __str__(self):
        customer_str = str(self.order.customer) if hasattr(self, 'order') and self.order else 'N/A'
        return f"{_('Factura')} {self.invoice_number} ({self.get_status_display()}) - {customer_str}"

class Payment(models.Model):
    """Registro de un pago asociado a una factura."""
    STATUS_CHOICES = [ ('PENDING', _('Pendiente')), ('COMPLETED', _('Completado')), ('FAILED', _('Fallido')), ('REFUNDED', _('Reembolsado')), ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name=_("Factura"))
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, help_text=_("Método utilizado para el pago"), verbose_name=_("Método de Pago"))
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT, help_text=_("Tipo de transacción (ej. pago, reembolso)"), verbose_name=_("Tipo Transacción"))
    date = models.DateTimeField(_("Fecha Pago"), default=timezone.now, help_text=_("Fecha y hora en que se registró el pago"))
    amount = models.DecimalField(_("Monto"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Moneda"), max_length=3, default='EUR')
    status = models.CharField(_("Estado"), max_length=20, choices=STATUS_CHOICES, default='COMPLETED', db_index=True)
    transaction_id = models.CharField(_("ID Transacción Externa"), max_length=100, blank=True, null=True, help_text=_("ID de la transacción externa si aplica"))
    notes = models.TextField(_("Notas"), blank=True, help_text=_("Notas sobre el pago"))

    class Meta:
        ordering = ['-date']
        verbose_name = _("Pago")
        verbose_name_plural = _("Pagos")

    def __str__(self):
        invoice_num = self.invoice.invoice_number if hasattr(self, 'invoice') else 'N/A'
        return f"{_('Pago')} ({self.get_status_display()}) de {self.amount} {self.currency} para {_('Factura')} {invoice_num}"

class CampaignService(models.Model):
    """Relación entre una campaña y un servicio incluido."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='included_services', verbose_name=_("Campaña"))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='campaign_assignments', verbose_name=_("Servicio"))
    discount_percentage = models.DecimalField(_("Descuento (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text=_("Descuento aplicado a este servicio en la campaña (%)"))
    additional_details = models.TextField(_("Detalles Adicionales"), null=True, blank=True)

    class Meta:
        unique_together = ('campaign', 'service')
        verbose_name = _("Servicio de Campaña")
        verbose_name_plural = _("Servicios de Campañas")

    def __str__(self):
        discount_str = f" ({self.discount_percentage}%)" if self.discount_percentage > 0 else ""
        service_name = self.service.name if hasattr(self, 'service') else 'N/A'
        campaign_name = self.campaign.campaign_name if hasattr(self, 'campaign') else 'N/A'
        return f"{_('Servicio')} {service_name} en {_('Campaña')} {campaign_name}{discount_str}"

class Provider(models.Model):
    """Proveedores o colaboradores externos."""
    name = models.CharField(_("Nombre Proveedor"), max_length=255, unique=True)
    contact_person = models.CharField(_("Persona de Contacto"), max_length=255, null=True, blank=True)
    email = models.EmailField(_("Email"), null=True, blank=True)
    phone = models.CharField(_("Teléfono"), max_length=30, null=True, blank=True)
    services_provided = models.ManyToManyField(
        Service, blank=True, related_name='providers',
        help_text=_("Servicios que ofrece este proveedor"), verbose_name=_("Servicios Ofrecidos")
    )
    rating = models.DecimalField(
        _("Calificación"), max_digits=3, decimal_places=1, default=Decimal('5.0'),
        help_text=_("Calificación interna (1-5)")
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    notes = models.TextField(_("Notas Internas"), blank=True, help_text=_("Notas internas sobre el proveedor"))

    class Meta:
        verbose_name = _("Proveedor")
        verbose_name_plural = _("Proveedores")
        ordering = ['name']

    def __str__(self):
        status = _("[ACTIVO]") if self.is_active else _("[INACTIVO]")
        return f"{self.name} {status}"

class Notification(models.Model):
    """Notificaciones para usuarios."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("Usuario"))
    message = models.TextField(_("Mensaje"))
    read = models.BooleanField(_("Leída"), default=False, db_index=True)
    created_at = models.DateTimeField(_("Fecha Creación"), auto_now_add=True)
    link = models.URLField(_("Enlace"), null=True, blank=True, help_text=_("Enlace relevante (ej. a un pedido, tarea)"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notificación")
        verbose_name_plural = _("Notificaciones")

    def __str__(self):
        status = _("[Leída]") if self.read else _("[No Leída]")
        username = self.user.username if hasattr(self, 'user') else 'N/A'
        return f"{_('Notificación')} para {username} {status}: {self.message[:50]}..."

class AuditLog(models.Model):
    """Registro de auditoría de acciones importantes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs', verbose_name=_("Usuario")
    )
    action = models.CharField(
        _("Acción"), max_length=255, help_text=_("Descripción de la acción realizada")
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    details = models.JSONField(
        _("Detalles"), default=dict, blank=True, help_text=_("Detalles adicionales en formato JSON")
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Registro de Auditoría")
        verbose_name_plural = _("Registros de Auditoría")

    def __str__(self):
        user_str = self.user.username if self.user else _("Sistema")
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else 'N/A'
        return f"{timestamp_str} - {user_str}: {self.action}"

# ==============================================================================
# ---------------------- MÉTODOS AÑADIDOS AL MODELO USER ----------------------
# ==============================================================================

UserModel = get_user_model()

# --- Propiedades y Métodos para Roles (Con Caché) ---
@property
def primary_role(self):
    cache_key = '_primary_role_cache'
    if not hasattr(self, cache_key):
        role = None
        try:
            profile = getattr(self, 'profile', None)
            if profile and profile.primary_role and profile.primary_role.is_active:
                role = profile.primary_role
        except Exception: pass # Captura genérica por si profile no es UserProfile
        setattr(self, cache_key, role)
    return getattr(self, cache_key)

@property
def primary_role_name(self):
    role = self.primary_role; return role.name if role else None

@property
def get_secondary_active_roles(self):
    cache_key = '_secondary_roles_cache'
    if not hasattr(self, cache_key):
        primary_role_id = None
        try: primary_role_id = self.profile.primary_role_id
        except Exception: pass
        qs = UserRole.objects.none()
        if self.pk:
             qs = UserRole.objects.filter(secondary_assignments__user_id=self.pk, secondary_assignments__is_active=True, is_active=True).distinct()
             if primary_role_id: qs = qs.exclude(id=primary_role_id)
        setattr(self, cache_key, qs)
    return getattr(self, cache_key)

@property
def get_secondary_active_role_names(self):
    return list(self.get_secondary_active_roles.values_list('name', flat=True))

@property
def get_all_active_role_names(self):
    all_roles = set(self.get_secondary_active_role_names)
    p_role_name = self.primary_role_name
    if p_role_name: all_roles.add(p_role_name)
    return list(all_roles)

def has_role(self, role_name):
    if not role_name: return False
    if self.primary_role_name == role_name: return True
    return role_name in self.get_secondary_active_role_names

def is_dragon(self):
    # Asegurarse que Roles.DRAGON existe antes de llamar a has_role
    dragon_role_name = getattr(Roles, 'DRAGON', None)
    return self.has_role(dragon_role_name) if dragon_role_name else False

UserModel.add_to_class("primary_role", primary_role)
UserModel.add_to_class("primary_role_name", primary_role_name)
UserModel.add_to_class("get_secondary_active_roles", get_secondary_active_roles)
UserModel.add_to_class("get_secondary_active_role_names", get_secondary_active_role_names)
UserModel.add_to_class("get_all_active_role_names", get_all_active_role_names)
UserModel.add_to_class("has_role", has_role)
UserModel.add_to_class("is_dragon", is_dragon)


# ==============================================================================
# ---------------------- SEÑALES DE LA APLICACIÓN -----------------------------
# ==============================================================================

# --- Señal para crear UserProfile ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_signal(sender, instance, created, **kwargs):
    if created: UserProfile.objects.get_or_create(user=instance)

# --- Señal para crear Customer/Employee ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_or_employee_profile_signal(sender, instance, created, **kwargs):
    if created:
        has_employee = Employee.objects.filter(user=instance).exists()
        has_customer = Customer.objects.filter(user=instance).exists()
        if not has_employee and not has_customer:
            if instance.is_staff: Employee.objects.get_or_create(user=instance)
            else: Customer.objects.get_or_create(user=instance)

# --- Señales de Pedidos ---
@receiver(post_save, sender=OrderService)
@receiver(post_delete, sender=OrderService)
def update_order_total_on_service_change_signal(sender, instance, **kwargs):
    if instance.order_id:
        try:
            order = Order.objects.get(pk=instance.order_id)
            order.update_total_amount()
        except Order.DoesNotExist: logger.warning(f"Order {instance.order_id} no encontrada al actualizar total desde OrderService {instance.id}. Posiblemente eliminada.")
        except Exception as e: logger.error(f"Error inesperado actualizando total de Order {instance.order_id} desde OrderService {instance.id}: {e}")

@receiver(pre_save, sender=Order)
def set_order_completion_date_signal(sender, instance, **kwargs):
    original_instance = None
    if instance.pk:
        try: original_instance = Order.objects.get(pk=instance.pk)
        except Order.DoesNotExist: pass
    if not instance.pk or original_instance:
        original_status = original_instance.status if original_instance else None
        if instance.status == 'DELIVERED' and original_status != 'DELIVERED': instance.completed_at = timezone.now()
        elif instance.status != 'DELIVERED' and (original_status == 'DELIVERED' or (not instance.pk and instance.status != 'DELIVERED')): instance.completed_at = None # Limpiar si ya no está entregado
        # elif not instance.pk and instance.status == 'DELIVERED': instance.completed_at = timezone.now() # Cubierto por primer if si status es DELIVERED

# --- Señales de Pagos y Facturas ---
@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def update_invoice_status_on_payment_signal(sender, instance, **kwargs):
    if instance.invoice_id:
        try:
            invoice = Invoice.objects.select_related('order__customer__user').get(pk=instance.invoice_id) # Optimizar
            invoice.update_paid_amount_and_status()
        except Invoice.DoesNotExist: logger.warning(f"Invoice {instance.invoice_id} no encontrada al actualizar estado desde Payment {instance.id}. Posiblemente eliminada.")
        except Exception as e: logger.error(f"Error inesperado actualizando estado de Invoice {instance.invoice_id} desde Payment {instance.id}: {e}")

# --- Helper Función Global para Notificaciones ---
def create_notification(user_recipient, message, link_obj=None):
    UserModelForCheck = get_user_model()
    if not user_recipient or not isinstance(user_recipient, UserModelForCheck): return
    link_url = None
    if link_obj and hasattr(link_obj, 'pk') and link_obj.pk:
        try:
            model_name = link_obj.__class__.__name__.lower(); app_label = link_obj._meta.app_label
            link_url = reverse(f'admin:{app_label}_{model_name}_change', args=[link_obj.pk])
        except Exception: pass # Silenciar error si URL no se puede generar
    try: Notification.objects.create(user=user_recipient, message=message, link=link_url)
    except Exception as e: logger.error(f"Error al crear notificación para {user_recipient.username}: {e}")

# --- Señales de Auditoría ---
def log_action(instance, action_verb, details_dict=None):
    user = get_current_user(); model_name = instance.__class__.__name__
    try: instance_str = str(instance)
    except Exception: instance_str = f"ID {instance.pk}" if instance.pk else "objeto no guardado/eliminado"
    action_str = f"{model_name} {action_verb}: {instance_str}"
    log_details = {'model': model_name, 'pk': instance.pk if instance.pk else None, 'representation': instance_str}
    if details_dict: log_details.update(details_dict)
    try: AuditLog.objects.create(user=user, action=action_str, details=log_details)
    except Exception as e: logger.error(f"Error al crear AuditLog: {e}")

AUDITED_MODELS = [Order, Invoice, Deliverable, Customer, Employee, Service, Payment, Provider, Campaign, UserProfile, UserRoleAssignment]

@receiver(post_save)
def audit_log_save_signal(sender, instance, created, **kwargs):
    if sender in AUDITED_MODELS:
        action_verb = "Creado" if created else "Actualizado"; details = {}
        if hasattr(instance, 'status'): status_val = getattr(instance, 'status', None); display_method = getattr(instance, 'get_status_display', None); details['status'] = display_method() if callable(display_method) else status_val
        if isinstance(instance, UserProfile) and instance.primary_role: details['primary_role'] = instance.primary_role.name
        if isinstance(instance, UserRoleAssignment) and instance.role: details['role'] = instance.role.name; details['assignment_active'] = instance.is_active
        log_action(instance, action_verb, details)

@receiver(post_delete)
def audit_log_delete_signal(sender, instance, **kwargs):
    if sender in AUDITED_MODELS: log_action(instance, "Eliminado")

# --- Señales de Notificación ---
@receiver(post_save, sender=Deliverable)
def notify_deliverable_signal(sender, instance, created, **kwargs):
    original_instance = None; assigned_employee_changed = False; status_changed = False
    current_assigned_employee_id = instance.assigned_employee_id # Cachear ID actual

    if not created and instance.pk:
        try: original_instance = Deliverable.objects.select_related('assigned_employee').get(pk=instance.pk)
        except Deliverable.DoesNotExist: pass

    if original_instance:
         if current_assigned_employee_id != original_instance.assigned_employee_id: assigned_employee_changed = True
         original_status = original_instance.status
         if original_status != instance.status: status_changed = True
    elif created: # Si es nuevo
        if current_assigned_employee_id: assigned_employee_changed = True # Se asignó al crear
        status_changed = True # El status siempre cambia de 'nada' a 'PENDING' (o lo que sea)
    else: original_status = None; status_changed = True # Caso raro: sin pk pero no creado

    # Notificar nueva asignación
    if assigned_employee_changed and instance.assigned_employee:
        if hasattr(instance.assigned_employee, 'user') and instance.assigned_employee.user:
            message = f"Te han asignado la tarea '{instance.description[:50]}...' del Pedido #{instance.order_id}"
            create_notification(instance.assigned_employee.user, message, instance)
        else: logger.warning(f"Empleado asignado ID {current_assigned_employee_id} a Deliverable {instance.id} no tiene usuario.")

    # Notificar cambio de estado relevante
    if status_changed:
        recipient, message = None, None
        try:
            # Solo notificar cambios de estado específicos, no todos
            notify_states = ['PENDING_APPROVAL', 'REVISION_REQUESTED', 'REQUIRES_INFO', 'APPROVED', 'COMPLETED'] # Estados que podrían generar notificación
            if instance.status in notify_states:
                if instance.status == 'PENDING_APPROVAL' and instance.order.customer:
                     recipient = instance.order.customer.user
                     message = f"La tarea '{instance.description[:50]}...' del Pedido #{instance.order_id} está lista para tu aprobación."
                elif instance.status in ['REVISION_REQUESTED', 'REQUIRES_INFO'] and instance.assigned_employee and hasattr(instance.assigned_employee, 'user'):
                     recipient = instance.assigned_employee.user
                     message = f"La tarea '{instance.description[:50]}...' (Pedido #{instance.order_id}) requiere tu atención: {instance.get_status_display()}."
                elif instance.status == 'APPROVED' and instance.assigned_employee and hasattr(instance.assigned_employee, 'user'):
                      recipient = instance.assigned_employee.user # Notificar al empleado que se aprobó? O al cliente?
                      message = f"La tarea '{instance.description[:50]}...' (Pedido #{instance.order_id}) ha sido aprobada."
                # Añadir más lógica según necesites
            if recipient and message: create_notification(recipient, message, instance)
        except Order.DoesNotExist: logger.warning(f"Orden {instance.order_id} no encontrada al notificar sobre Deliverable {instance.id}")
        except Exception as e: logger.error(f"Error procesando notificación para Deliverable {instance.id}: {e}")

===== permissions.py =====

# api/permissions.py
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions # <--- ¡IMPORTACIÓN AÑADIDA!

# Importar constantes de roles
try:
    from .roles import Roles
except ImportError:
    class Roles:
        DRAGON = 'dragon'; ADMIN = 'admin'; MARKETING = 'mktg'; FINANCE = 'fin';
        SALES = 'sales'; DEVELOPMENT = 'dev'; SUPPORT = 'support'; OPERATIONS = 'ops';
        DESIGN = 'design'; AUDIOVISUAL = 'av';
    print("ADVERTENCIA: api/roles.py no encontrado. Usando roles placeholder.")

# Importar modelos si son necesarios
# from .models import Order, Customer

# ==============================================================================
# ------------------------- PERMISOS PERSONALIZADOS --------------------------
# ==============================================================================

class HasRolePermission(BasePermission):
    required_roles = []
    message = _("No tienes permiso para realizar esta acción debido a tu rol.")

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_has_required_role = False
        if hasattr(request.user, 'has_role'):
            user_has_required_role = any(request.user.has_role(role) for role in self.required_roles)
        elif hasattr(request.user, 'get_all_active_role_names'):
             try:
                 user_roles = set(request.user.get_all_active_role_names)
                 user_has_required_role = any(role in user_roles for role in self.required_roles)
             except Exception:
                 pass
        return request.user.is_staff or user_has_required_role

# --- Subclases específicas ---
class CanAccessDashboard(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.FINANCE, Roles.MARKETING, Roles.SALES, Roles.OPERATIONS]
    message = _("No tienes permiso para acceder al dashboard.")

class IsAdminOrDragon(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON]
    message = _("Necesitas ser Administrador o Dragón para esta acción.")

class CanManageEmployees(IsAdminOrDragon):
    message = _("No tienes permiso para gestionar empleados.")

class CanManageJobPositions(IsAdminOrDragon):
     message = _("No tienes permiso para gestionar puestos de trabajo.")

class CanManageCampaigns(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.MARKETING]
    message = _("No tienes permiso para gestionar campañas.")

class CanManageServices(IsAdminOrDragon):
    message = _("No tienes permiso para gestionar servicios.")

class CanManageFinances(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.FINANCE]
    message = _("No tienes permiso para realizar operaciones financieras.")

class CanViewAllOrders(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES, Roles.SUPPORT, Roles.OPERATIONS]
    message = _("No tienes permiso para ver todos los pedidos.")

class CanCreateOrders(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES]
    message = _("No tienes permiso para crear pedidos.")

class CanViewAllDeliverables(IsAdminOrDragon):
     message = _("No tienes permiso para ver todos los entregables.")

class CanCreateDeliverables(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.DEVELOPMENT, Roles.DESIGN, Roles.AUDIOVISUAL, Roles.OPERATIONS]
    message = _("No tienes permiso para crear entregables.")

class CanViewFormResponses(HasRolePermission):
    required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SALES, Roles.SUPPORT]
    message = _("No tienes permiso para ver las respuestas de formularios.")

class CanViewAuditLogs(IsAdminOrDragon):
    message = _("No tienes permiso para ver los registros de auditoría.")

# --- Permisos adicionales ---

class IsOwnerOrReadOnly(BasePermission):
    """
    Permiso a nivel de objeto para permitir solo a los propietarios de un objeto editarlo.
    Asume que el objeto tiene un atributo 'user' o 'customer.user'.
    """
    def has_object_permission(self, request, view, obj):
        # La corrección está aquí: se usa 'permissions.SAFE_METHODS' importado arriba
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        owner = getattr(obj, 'user', None) or getattr(getattr(obj, 'customer', None), 'user', None)
        return owner == request.user

class IsCustomerOwnerOrAdminOrSupport(BasePermission):
    message = _("No tienes permiso para acceder a este cliente.")

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'customer_profile') and obj == request.user.customer_profile:
            return True
        if hasattr(request.user, 'employee_profile'):
            required_roles = [Roles.ADMIN, Roles.DRAGON, Roles.SUPPORT, Roles.SALES]
            if hasattr(request.user, 'has_role'):
                 if any(request.user.has_role(role) for role in required_roles):
                     return True
            elif request.user.is_staff:
                 return True
        return False

===== roles.py =====

# api/roles.py
"""
Define constantes para los nombres internos de los roles de usuario.
Esto evita errores tipográficos y hace el código más legible.
"""

class Roles:
    # Core / Admin Roles
    DRAGON = 'dragon'        # Superusuario específico de la app con acceso total
    ADMIN = 'admin'          # Administrador general de la aplicación

    # Department / Function Roles (Primarios Típicos)
    MARKETING = 'mktg'       # Equipo de Marketing
    FINANCE = 'fin'          # Equipo de Finanzas
    SALES = 'sales'          # Equipo de Ventas
    DEVELOPMENT = 'dev'      # Equipo de Desarrollo
    AUDIOVISUAL = 'avps'     # Equipo de Producción Audiovisual
    DESIGN = 'dsgn'          # Equipo de Diseño
    SUPPORT = 'support'      # Equipo de Soporte al Cliente
    OPERATIONS = 'ops'       # Equipo de Operaciones Internas
    HR = 'hr'                # Recursos Humanos (Ejemplo adicional)

    # Podrías añadir roles secundarios/permisos aquí si los necesitas muy definidos
    # REPORT_VIEWER = 'report_viewer'
    # CONTENT_PUBLISHER = 'content_publisher'

    # Puedes añadir un método para obtener una lista o diccionario si es útil
    @classmethod
    def get_all_roles(cls):
        return [getattr(cls, attr) for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("__")]

# FIN DE base_models_api.txt
```

### 2.2. Vistas Antiguas (`views_.txt`)

```python
# <CONTENIDO COMPLETO DE views_.txt>
# COMIENZO DE views_.txt

# File: users.py
# api/views/users.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model

# --- Importaciones de Serializers Corregidas ---
from ..serializers.base import BasicUserSerializer # Importar desde base.py
# ----------------------------------------------

User = get_user_model()

class UserMeView(APIView):
    """
    Devuelve los datos del usuario actualmente autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Obtiene y serializa los datos del usuario logueado.
        """
        try:
            user = User.objects.select_related(
                'profile__primary_role',
                'employee_profile__position'
            ).get(pk=request.user.pk)
        except User.DoesNotExist:
             return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except AttributeError as e:
             print(f"Advertencia: Error al acceder a relaciones en UserMeView para usuario {request.user.pk}: {e}")
             user = request.user

        # Usa el BasicUserSerializer importado correctamente
        serializer = BasicUserSerializer(user, context={'request': request})
        return Response(serializer.data)

# Si añades UserViewSet u otras vistas aquí que usen UserCreateSerializer, UserRoleSerializer, etc.
# deberás importarlos desde ..serializers.users
# from ..serializers.users import UserCreateSerializer, UserRoleSerializer, UserRoleAssignmentSerializer

# File: services_catalog.py
# api/views/services_catalog.py
from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend

# Importaciones relativas
from ..models import ServiceCategory, Service, Campaign # Quitar Feature/Price si no hay ViewSet para ellos
from ..permissions import AllowAny, CanManageServices, CanManageCampaigns, IsAdminOrDragon

# --- Importaciones de Serializers Corregidas ---
from ..serializers.services_catalog import (
    ServiceCategorySerializer, ServiceSerializer, CampaignSerializer
    # Quitar Price/Feature/CampaignService si no hay ViewSet para ellos
    # PriceSerializer, ServiceFeatureSerializer, CampaignServiceSerializer
)
# ----------------------------------------------


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para listar y ver categorías de servicios.
    """
    queryset = ServiceCategory.objects.prefetch_related('services').all()
    # Usa el serializer importado correctamente
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Servicios.
    """
    queryset = Service.objects.select_related(
        'category',
        'campaign'
    ).prefetch_related(
        'features',
        'price_history'
    ).all()
    # Usa el serializer importado correctamente
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'category': ['exact'], 'category__name': ['exact', 'icontains'],
        'is_active': ['exact'], 'is_package': ['exact'],
        'is_subscription': ['exact'], 'name': ['icontains'],
        'ventulab': ['exact'], 'campaign': ['exact', 'isnull'],
    }

    def get_permissions(self):
        """ Permisos: Lectura pública, escritura restringida. """
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [CanManageServices]
        return super().get_permissions()


class CampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Campañas de marketing/promocionales.
    """
    queryset = Campaign.objects.prefetch_related(
        'campaignservice_set__service' # Ajustar related_name si es diferente
    ).all()
    # Usa el serializer importado correctamente
    serializer_class = CampaignSerializer
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'is_active': ['exact'],
        'start_date': ['date', 'date__gte', 'date__lte'],
        'end_date': ['date', 'date__gte', 'date__lte', 'isnull'],
        'name': ['icontains'],
    }

# File: orders.py
# api/views/orders.py
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import Order, Deliverable, Customer, Employee
from ..permissions import (
    IsAuthenticated, CanViewAllOrders, CanCreateOrders,
    CanViewAllDeliverables, CanCreateDeliverables, IsOwnerOrReadOnly,
    IsCustomerOwnerOrAdminOrSupport
)

# --- Importaciones de Serializers Corregidas ---
from ..serializers.orders import (
    OrderReadSerializer, OrderCreateUpdateSerializer, DeliverableSerializer
)
# Nota: OrderService serializers son usados internamente por Order serializers,
# no necesitan importarse aquí a menos que los uses directamente en la vista.
# ----------------------------------------------

logger = logging.getLogger(__name__)
User = get_user_model()

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Pedidos (Orders).
    """
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'customer__user__username': ['exact', 'icontains'],
        'customer__company_name': ['icontains'],
        'priority': ['exact', 'in'],
        'employee__user__username': ['exact', 'icontains'],
        'date_received': ['date', 'date__gte', 'date__lte', 'year', 'month'],
        'date_required': ['date', 'date__gte', 'date__lte', 'isnull'],
        'id': ['exact']
    }

    def get_serializer_class(self):
        """ Usa serializer de lectura para list/retrieve, y de escritura para otros. """
        # Usa los serializers importados correctamente
        if self.action in ['list', 'retrieve']:
            return OrderReadSerializer
        return OrderCreateUpdateSerializer

    def get_queryset(self):
        # ... (lógica sin cambios) ...
        user = self.request.user
        base_qs = Order.objects.select_related(
            'customer', 'customer__user', 'employee', 'employee__user'
        ).prefetch_related('services__service', 'deliverables')

        if hasattr(user, 'customer_profile') and user.customer_profile:
            return base_qs.filter(customer=user.customer_profile)
        elif hasattr(user, 'employee_profile') and user.employee_profile:
            checker = CanViewAllOrders()
            if checker.has_permission(request=self.request, view=self):
                return base_qs.all()
            else:
                return base_qs.filter(employee=user.employee_profile)
        else:
            logger.warning(f"Usuario {user.username} sin perfil de cliente o empleado válido intentó listar pedidos.")
            return Order.objects.none()

    def perform_create(self, serializer):
        # ... (lógica sin cambios) ...
        user = self.request.user
        customer_data = serializer.validated_data.get('customer')

        if hasattr(user, 'employee_profile') and user.employee_profile:
            checker = CanCreateOrders()
            if not checker.has_permission(request=self.request, view=self):
                raise PermissionDenied(checker.message)
            employee_to_assign = serializer.validated_data.get('employee', user.employee_profile)
            # Guarda usando el OrderCreateUpdateSerializer.create
            serializer.save(employee=employee_to_assign)
        elif hasattr(user, 'customer_profile') and user.customer_profile:
            if customer_data and customer_data != user.customer_profile:
                raise PermissionDenied(_("No puedes crear pedidos para otros clientes."))
            # Guarda usando el OrderCreateUpdateSerializer.create
            serializer.save(customer=user.customer_profile, employee=None)
        else:
            raise PermissionDenied(_("Tu perfil de usuario no es válido para crear pedidos."))

    # perform_update usa OrderCreateUpdateSerializer.update por defecto


class DeliverableViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Entregables (Deliverables) asociados a un Pedido.
    """
    # Usa el serializer importado correctamente
    serializer_class = DeliverableSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'assigned_employee': ['exact', 'isnull'],
        'assigned_provider': ['exact', 'isnull'],
        'due_date': ['date', 'date__gte', 'date__lte', 'isnull'],
        'order': ['exact'],
        'order__customer__user__username': ['exact', 'icontains'],
        'assigned_employee__user__username': ['exact', 'icontains'],
    }

    def get_queryset(self):
        # ... (lógica sin cambios) ...
        user = self.request.user
        order_pk = self.kwargs.get('order_pk')

        base_qs = Deliverable.objects.select_related(
            'order', 'order__customer', 'order__customer__user',
            'order__employee', 'order__employee__user',
            'assigned_employee', 'assigned_employee__user', 'assigned_provider'
        )

        if order_pk:
            order = get_object_or_404(Order.objects.select_related('customer', 'employee'), pk=order_pk)
            can_view_order = False
            if hasattr(user, 'customer_profile') and order.customer == user.customer_profile:
                can_view_order = True
            elif hasattr(user, 'employee_profile') and user.employee_profile:
                 order_viewer_checker = CanViewAllOrders()
                 if order_viewer_checker.has_permission(self.request, self) or order.employee == user.employee_profile:
                      can_view_order = True

            if not can_view_order:
                 return Deliverable.objects.none()
            return base_qs.filter(order=order)

        else:
            if hasattr(user, 'customer_profile') and user.customer_profile:
                return base_qs.filter(order__customer=user.customer_profile)
            elif hasattr(user, 'employee_profile') and user.employee_profile:
                viewer_checker = CanViewAllDeliverables()
                if viewer_checker.has_permission(request=self.request, view=self):
                    return base_qs.all()
                else:
                    return base_qs.filter(assigned_employee=user.employee_profile)
            else:
                return Deliverable.objects.none()


    def perform_create(self, serializer):
        # ... (lógica sin cambios) ...
        user = self.request.user
        order_pk = self.kwargs.get('order_pk')

        if not order_pk:
            raise ValidationError({"detail": _("La creación de entregables debe hacerse a través de la ruta de un pedido específico (e.g., /api/orders/ID/deliverables/).")})

        order = get_object_or_404(Order, pk=order_pk)
        creator_checker = CanCreateDeliverables()
        if not creator_checker.has_permission(request=self.request, view=self):
             raise PermissionDenied(creator_checker.message)

        # El serializer se encarga de guardar el archivo si se envió
        serializer.save(order=order)

# File: customers.py
# api/views/customers.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import Customer
from ..permissions import IsCustomerOwnerOrAdminOrSupport

# --- Importaciones de Serializers Corregidas ---
from ..serializers.customers import CustomerSerializer, CustomerCreateSerializer
# ----------------------------------------------

User = get_user_model()

class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Clientes (Customers).
    """
    queryset = Customer.objects.select_related(
        'user',
        'user__profile__primary_role'
    ).all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user__email', 'preferred_contact_method', 'country', 'company_name']

    def get_serializer_class(self):
        """ Devuelve el serializer apropiado según la acción. """
        # Usa los serializers importados correctamente
        if self.action == 'create':
            return CustomerCreateSerializer
        return CustomerSerializer

    def get_permissions(self):
        """ Define los permisos según la acción. """
        if self.action == 'create':
            self.permission_classes = [permissions.AllowAny]
        elif self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated] # Ajusta si es necesario
        else:
            self.permission_classes = [IsCustomerOwnerOrAdminOrSupport]
        return super().get_permissions()

    # perform_create ahora puede devolver la instancia creada,
    # y DRF usará el serializer definido en get_serializer_class para la respuesta.
    def perform_create(self, serializer):
        # La lógica de creación está en CustomerCreateSerializer.create
        # Solo necesitamos guardar y DRF se encarga del resto.
        serializer.save() # Devuelve la instancia creada


# File: utilities.py
# api/views/utilities.py
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import Notification, AuditLog
from ..permissions import IsAuthenticated, CanViewAuditLogs, IsAdminOrDragon

# --- Importaciones de Serializers Corregidas ---
from ..serializers.utilities import NotificationSerializer, AuditLogSerializer
# ----------------------------------------------

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Notificaciones de usuario.
    """
    # Usa el serializer importado correctamente
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Filtra las notificaciones para mostrar solo las del usuario actual. """
        user_instance = self.request.user
        return Notification.objects.filter(user=user_instance).order_by('-created_at')

    def perform_update(self, serializer):
         # ... (lógica sin cambios) ...
         return Response({"detail": "Acción no permitida. Usa 'mark-read'."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_destroy(self, instance):
        # ... (lógica sin cambios) ...
        if instance.user != self.request.user:
             return Response(status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        logger.info(f"Notificación {instance.id} eliminada por usuario {self.request.user.username}")


    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request, pk=None):
        # ... (lógica sin cambios) ...
        notification = self.get_object()
        if not notification.read:
            notification.read = True
            notification.save(update_fields=['read'])
            logger.debug(f"Notificación {pk} marcada como leída por {request.user.username}")
        # Usa el serializer de la clase (NotificationSerializer)
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_as_read(self, request):
        # ... (lógica sin cambios) ...
        queryset = self.get_queryset().filter(read=False)
        updated_count = queryset.update(read=True)
        logger.info(f"{updated_count} notificaciones marcadas como leídas para {request.user.username}")
        return Response({'status': f'{updated_count} notificaciones marcadas como leídas'})

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        # ... (lógica sin cambios) ...
        count = self.get_queryset().filter(read=False).count()
        return Response({'unread_count': count})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para ver los Registros de Auditoría (Audit Logs).
    """
    queryset = AuditLog.objects.select_related('user').all().order_by('-timestamp')
    # Usa el serializer importado correctamente
    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAuditLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'user__username': ['exact', 'icontains'],
        'action': ['exact', 'icontains'],
        'timestamp': ['date', 'date__gte', 'date__lte', 'year', 'month', 'time__gte', 'time__lte'],
        'target_model': ['exact', 'icontains'],
        'target_id': ['exact'],
        'ip_address': ['exact'],
    }

# File: authentication.py
# api/views/authentication.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.contrib.auth import get_user_model

# --- Importaciones de Serializers Corregidas ---
# Importar desde los nuevos módulos específicos
from ..serializers.authentication import CustomTokenObtainPairSerializer
from ..serializers.base import BasicUserSerializer
# ----------------------------------------------

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT, usando el serializer customizado.
    """
    # El serializer_class ahora apunta al importado correctamente
    serializer_class = CustomTokenObtainPairSerializer

class CheckAuthView(APIView):
    """
    Verifica si el usuario actual está autenticado y devuelve sus datos básicos.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Devuelve el estado de autenticación y los datos del usuario.
        """
        try:
            user = User.objects.select_related(
                'profile__primary_role',
                'employee_profile__position'
            ).get(pk=request.user.pk)
        except User.DoesNotExist:
             return Response({"isAuthenticated": False, "user": None}, status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError as e:
             print(f"Advertencia: Error al acceder a relaciones en CheckAuthView para usuario {request.user.pk}: {e}")
             user = request.user

        # Usa el BasicUserSerializer importado correctamente
        serializer = BasicUserSerializer(user, context={'request': request})
        data = {"isAuthenticated": True, "user": serializer.data}
        return Response(data)

# File: employees.py
# api/views/employees.py
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import Employee, JobPosition
from ..permissions import CanManageEmployees, CanManageJobPositions, IsAdminOrDragon

# --- Importaciones de Serializers Corregidas ---
from ..serializers.employees import (
    EmployeeSerializer, EmployeeCreateSerializer, JobPositionSerializer
)
# ----------------------------------------------

User = get_user_model()

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Empleados (Employees).
    """
    queryset = Employee.objects.select_related(
        'user',
        'user__profile__primary_role',
        'position'
    ).prefetch_related(
        'user__secondary_role_assignments__role'
    ).filter(user__is_active=True)
    permission_classes = [CanManageEmployees]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'position__name': ['exact', 'icontains'],
        'user__username': ['exact', 'icontains'],
        'user__email': ['exact', 'icontains'],
        'user__first_name': ['icontains'],
        'user__last_name': ['icontains'],
        'user__profile__primary_role__name': ['exact', 'icontains'],
        'user__is_active': ['exact']
    }

    def get_serializer_class(self):
        """ Usa un serializer diferente para la creación. """
        # Usa los serializers importados correctamente
        if self.action == 'create':
            return EmployeeCreateSerializer
        return EmployeeSerializer

    # Similar a CustomerViewSet, puedes sobrescribir create si necesitas
    # devolver la instancia creada usando EmployeeSerializer en lugar de EmployeeCreateSerializer
    # (aunque el comportamiento por defecto suele ser suficiente).
    def perform_create(self, serializer):
        serializer.save()


class JobPositionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Puestos de Trabajo (Job Positions).
    """
    queryset = JobPosition.objects.all()
    # Usa el serializer importado correctamente
    serializer_class = JobPositionSerializer
    permission_classes = [CanManageJobPositions]

# File: dashboard.py
# api/views/dashboard.py
import logging
from decimal import Decimal
from datetime import timedelta, datetime
from collections import defaultdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import (
    Sum, Count, Q, F, Avg, OuterRef, Subquery, ExpressionWrapper,
    DurationField, DecimalField, Case, When, Value, CharField
)
from django.db.models.functions import TruncMonth, Coalesce, Now
from django.contrib.auth import get_user_model # <--- IMPORTACIÓN AÑADIDA

# Importaciones relativas
from ..models import (
    Customer, Order, OrderService, Deliverable, Employee, Invoice, Payment, Service
    # 'User' eliminado de esta lista
)
from ..permissions import CanAccessDashboard

logger = logging.getLogger(__name__)
User = get_user_model() # <--- OBTENER MODELO User

class DashboardDataView(APIView):
    """
    Proporciona datos agregados y KPIs para mostrar en el dashboard principal.
    """
    permission_classes = [IsAuthenticated, CanAccessDashboard]

    def get(self, request, *args, **kwargs):
        # --- Log de Acceso ---
        user_roles_str = 'N/A'
        if hasattr(request.user, 'get_all_active_role_names'):
            try:
                roles_list = request.user.get_all_active_role_names
                user_roles_str = ', '.join(map(str, roles_list)) if isinstance(roles_list, (list, tuple, set)) else str(roles_list)
            except Exception as e:
                logger.warning(f"Error al obtener/formatear roles para log en Dashboard: {e}")
                user_roles_str = "[Error roles]"
        logger.info(f"[DashboardView] GET solicitado por {request.user.username} (Roles: {user_roles_str})")

        try:
            # --- Manejo de Fechas ---
            end_date_str = request.query_params.get('end_date', timezone.now().strftime('%Y-%m-%d'))
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()

            start_date_str = request.query_params.get('start_date')
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else end_date - timedelta(days=180)
            except ValueError:
                 start_date = end_date - timedelta(days=180)

            today = timezone.now().date()
            first_day_current_month = today.replace(day=1)
            last_day_prev_month = first_day_current_month - timedelta(days=1)
            first_day_prev_month = last_day_prev_month.replace(day=1)
            kpi_date_range = (first_day_prev_month, last_day_prev_month)

            one_year_ago = today - timedelta(days=365)
            fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)

            final_task_statuses = getattr(Deliverable, 'FINAL_STATUSES', ['COMPLETED', 'CANCELLED', 'ARCHIVED'])
            final_invoice_statuses = getattr(Invoice, 'FINAL_STATUSES', ['PAID', 'CANCELLED', 'VOID'])

            # --- Queries Optimizadas ---
            customer_demographics_qs = Customer.objects.filter(
                country__isnull=False
            ).exclude(
                country=''
            ).values('country').annotate(count=Count('id')).order_by('-count')
            customer_demographics_data = list(customer_demographics_qs)

            recent_orders_query = Order.objects.select_related(
                'customer__user', # Usa la relación user del modelo Customer
                'customer'
            ).order_by('-date_received')[:10]

            top_services_query = OrderService.objects.filter(
                order__date_received__date__range=(start_date, end_date),
                order__status='DELIVERED'
            ).values(
                'service__name', 'service__is_subscription'
            ).annotate(
                count=Count('id'),
                revenue=Coalesce(Sum(F('price') * F('quantity')), Decimal('0.00'), output_field=DecimalField())
            ).order_by('-count')[:10]
            top_services_data = list(top_services_query)

            payments_last_month = Payment.objects.filter(
                date__date__range=kpi_date_range,
                status='COMPLETED'
            )
            kpi_revenue_last_month = payments_last_month.aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
            )['total']

            completed_orders_last_month_count = Order.objects.filter(
                status='DELIVERED',
                completed_at__date__range=kpi_date_range
            ).count()

            kpi_aov = (kpi_revenue_last_month / completed_orders_last_month_count) if completed_orders_last_month_count > 0 else Decimal('0.00')

            kpi_subs_last_month_count = OrderService.objects.filter(
                order__date_received__date__range=kpi_date_range,
                service__is_subscription=True,
                order__status='DELIVERED'
            ).count()

            kpi_total_customers_count = Customer.objects.count()
            kpi_active_employees_count = Employee.objects.filter(user__is_active=True).count() # Usa relación user de Employee

            # Usa 'User' obtenido con get_user_model()
            active_users_count = User.objects.filter(
                last_login__gte=fifteen_minutes_ago,
                is_active=True
            ).count()

            top_customers_query = Payment.objects.filter(
                status='COMPLETED',
                date__date__range=(one_year_ago, today)
            ).values(
                'invoice__order__customer_id'
            ).annotate(
                customer_name=Subquery(
                    Customer.objects.filter(
                        pk=OuterRef('invoice__order__customer_id')
                    ).values(
                        name=Coalesce(
                            F('company_name'),
                            F('user__first_name'), # Usa relación user de Customer
                            F('user__username'),   # Usa relación user de Customer
                            output_field=CharField()
                        )
                    )[:1]
                ),
                total_revenue=Sum('amount')
            ).order_by('-total_revenue')[:5]
            top_customers_data = list(top_customers_query)

            task_summary = Deliverable.objects.aggregate(
                total_active=Count('id', filter=~Q(status__in=final_task_statuses)),
                unassigned=Count('id', filter=Q(assigned_employee__isnull=True) & Q(assigned_provider__isnull=True) & ~Q(status__in=final_task_statuses)),
                pending_approval=Count('id', filter=Q(status__in=['PENDING_APPROVAL', 'PENDING_INTERNAL_APPROVAL'])),
                requires_info=Count('id', filter=Q(status='REQUIRES_INFO')),
                assigned_to_provider=Count('id', filter=Q(assigned_provider__isnull=False) & ~Q(status__in=final_task_statuses)),
                overdue=Count('id', filter=Q(due_date__isnull=False, due_date__lt=today) & ~Q(status__in=final_task_statuses))
            )

            invoice_summary = Invoice.objects.filter(~Q(status='DRAFT')).aggregate(
                total_active=Count('id', filter=~Q(status__in=final_invoice_statuses)),
                pending=Count('id', filter=Q(status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE'])),
                paid_count=Count('id', filter=Q(status='PAID')),
                overdue_count=Count('id', filter=Q(status='OVERDUE'))
            )

            avg_duration_data = Order.objects.filter(
                status='DELIVERED',
                completed_at__isnull=False,
                date_received__isnull=False,
                completed_at__gte=F('date_received'),
                completed_at__date__range=(one_year_ago, today)
            ).aggregate(
                avg_duration=Avg(
                    ExpressionWrapper(F('completed_at') - F('date_received'), output_field=DurationField())
                )
            )
            avg_duration_days = avg_duration_data['avg_duration'].days if avg_duration_data['avg_duration'] else None

            employee_workload_query = Employee.objects.filter(
                user__is_active=True # Usa relación user de Employee
            ).annotate(
                active_tasks=Count('assigned_deliverables', filter=~Q(assigned_deliverables__status__in=final_task_statuses))
            ).values(
                'user__username',     # Usa relación user de Employee
                'user__first_name',   # Usa relación user de Employee
                'user__last_name',    # Usa relación user de Employee
                'active_tasks'
            ).order_by('-active_tasks')
            employee_workload_data = list(employee_workload_query)


            # --- Formateo de respuesta ---
            def get_customer_display_name(order):
                 if order.customer:
                     # Usa la relación 'user' del modelo Customer
                     user_obj = order.customer.user # Renombrado para evitar conflicto con User=get_user_model()
                     name_parts = [
                         order.customer.company_name,
                         user_obj.get_full_name() if user_obj and user_obj.get_full_name() else None,
                         user_obj.username if user_obj else None
                     ]
                     display_name = next((name for name in name_parts if name and name.strip()), None)
                     return display_name or _("Cliente ID {}").format(order.customer.id)
                 return _("Cliente Desconocido")

            formatted_recent_orders = []
            for o in recent_orders_query:
                try:
                    formatted_recent_orders.append({
                        'id': o.id,
                        'customer_name': get_customer_display_name(o),
                        'status': o.get_status_display(),
                        'date_received': o.date_received.isoformat() if o.date_received else None,
                        'total_amount': o.total_amount
                    })
                except Exception as e:
                    logger.error(f"[DashboardView] Error formateando orden reciente {o.id}: {e}", exc_info=True)
                    formatted_recent_orders.append({
                         'id': o.id, 'customer_name': 'Error al procesar', 'status': 'Error',
                         'date_received': None, 'total_amount': None
                    })

            # --- Ensamblaje Final de Datos ---
            dashboard_data = {
                'kpis': {
                    'revenue_last_month': kpi_revenue_last_month,
                    'subscriptions_last_month': kpi_subs_last_month_count,
                    'completed_orders_last_month': completed_orders_last_month_count,
                    'average_order_value_last_month': round(kpi_aov, 2) if kpi_aov else Decimal('0.00'),
                    'total_customers': kpi_total_customers_count,
                    'active_employees': kpi_active_employees_count,
                },
                'customer_demographics': customer_demographics_data,
                'recent_orders': formatted_recent_orders,
                'top_services': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'data': top_services_data
                },
                'active_users_now': active_users_count,
                'top_customers_last_year': top_customers_data,
                'task_summary': task_summary,
                'invoice_summary': invoice_summary,
                'average_order_duration_days': avg_duration_days,
                'employee_workload': employee_workload_data,
            }

            logger.info(f"[DashboardView] Datos generados exitosamente para {request.user.username}.")
            return Response(dashboard_data)

        except Exception as e:
             logger.error(f"[DashboardView] Error 500 inesperado para usuario {request.user.username}: {e}", exc_info=True)
             return Response({"detail": _("Ocurrió un error interno procesando los datos del dashboard.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# File: finances.py
# api/views/finances.py
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import Invoice, Payment, Order, Customer # Añadir Method/Type si hay ViewSet
from ..permissions import IsAuthenticated, CanManageFinances, IsCustomerOwnerOrAdminOrSupport

# --- Importaciones de Serializers Corregidas ---
from ..serializers.finances import (
    InvoiceSerializer, InvoiceBasicSerializer,
    PaymentReadSerializer, PaymentCreateSerializer
    # Añadir Method/Type si hay ViewSet para ellos
    # PaymentMethodSerializer, TransactionTypeSerializer
)
# ----------------------------------------------

logger = logging.getLogger(__name__)
User = get_user_model()

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Facturas (Invoices).
    """
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'order__customer__user__username': ['exact', 'icontains'],
        'order__customer__company_name': ['icontains'],
        'order__id': ['exact'],
        'date': ['date', 'date__gte', 'date__lte', 'year', 'month'],
        'due_date': ['date', 'date__gte', 'date__lte', 'isnull'],
        'invoice_number': ['exact', 'icontains'],
        'total_amount': ['exact', 'gte', 'lte'],
    }

    def get_serializer_class(self):
        """ Usa un serializer básico para la lista, completo para otros. """
        # Usa los serializers importados correctamente
        if self.action == 'list':
            return InvoiceBasicSerializer
        return InvoiceSerializer

    def get_queryset(self):
        # ... (lógica sin cambios) ...
        user = self.request.user
        base_qs = Invoice.objects.select_related(
            'order', 'order__customer', 'order__customer__user',
            'order__employee', 'order__employee__user'
        ).prefetch_related('payments__method')

        if hasattr(user, 'customer_profile') and user.customer_profile:
            return base_qs.filter(order__customer=user.customer_profile)
        elif hasattr(user, 'employee_profile'):
            checker = CanManageFinances()
            if checker.has_permission(request=self.request, view=self):
                return base_qs.all()
            else:
                return Invoice.objects.none()
        else:
            return Invoice.objects.none()

    def perform_create(self, serializer):
        # ... (lógica sin cambios) ...
        checker = CanManageFinances()
        if not checker.has_permission(request=self.request, view=self):
            raise PermissionDenied(checker.message)
        serializer.save() # InvoiceSerializer.create manejará la lógica

    def perform_update(self, serializer):
        # ... (lógica sin cambios) ...
        checker = CanManageFinances()
        if not checker.has_permission(request=self.request, view=self):
             raise PermissionDenied(checker.message)
        if hasattr(self.request.user, 'customer_profile'):
             raise PermissionDenied(_("Los clientes no pueden modificar facturas."))
        serializer.save() # InvoiceSerializer.update manejará la lógica

    def perform_destroy(self, instance):
        # ... (lógica sin cambios) ...
        checker = CanManageFinances()
        if not checker.has_permission(request=self.request, view=self):
             raise PermissionDenied(checker.message)
        if hasattr(self.request.user, 'customer_profile'):
             raise PermissionDenied(_("Los clientes no pueden eliminar facturas."))
        instance.delete()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Pagos (Payments).
    """
    queryset = Payment.objects.select_related(
        'invoice', 'invoice__order', 'invoice__order__customer',
        'invoice__order__customer__user', 'method', 'transaction_type'
    ).all()
    permission_classes = [CanManageFinances]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'status': ['exact', 'in'],
        'method': ['exact'], 'method__name': ['exact', 'icontains'],
        'transaction_type': ['exact'], 'transaction_type__name': ['exact', 'icontains'],
        'currency': ['exact'],
        'invoice__invoice_number': ['exact', 'icontains'],
        'invoice__order__id': ['exact'],
        'invoice__order__customer__user__username': ['exact', 'icontains'],
        'date': ['date', 'date__gte', 'date__lte', 'year', 'month'],
        'amount': ['exact', 'gte', 'lte'],
    }

    def get_serializer_class(self):
        """ Serializer de lectura para list/retrieve, de creación/edición para otros. """
        # Usa los serializers importados correctamente
        if self.action in ['list', 'retrieve']:
            return PaymentReadSerializer
        return PaymentCreateSerializer

    # La lógica de actualizar estado de factura se movió a PaymentCreateSerializer.save()
    # o se puede manejar con señales post_save/post_delete en el modelo Payment.
    # Estos métodos perform_* solo necesitan llamar a serializer.save() o instance.delete().

    def perform_create(self, serializer):
        # La lógica de validación y posible actualización de factura está en el serializer
        serializer.save()

    def perform_update(self, serializer):
        # La lógica de validación y posible actualización de factura está en el serializer
        serializer.save()

    def perform_destroy(self, instance):
        # La lógica para actualizar factura post-delete debería estar en una señal
        invoice = instance.invoice # Guardar referencia si la señal la necesita
        payment_id = instance.id
        instance.delete()
        # Idealmente, una señal post_delete en Payment llamaría a invoice.update_status()
        # logger.info(f"Estado de factura {invoice.id} actualizado tras eliminación de pago {payment_id}")

# File: forms.py
# api/views/forms.py
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Importaciones relativas
from ..models import FormResponse, Form, FormQuestion, Customer
from ..permissions import IsAuthenticated, CanViewFormResponses, IsAdminOrDragon
from ..services import FormResponseService

# --- Importaciones de Serializers Corregidas ---
from ..serializers.forms import (
    FormResponseSerializer, FormResponseBulkCreateSerializer
    # Añadir Form/Question si hay ViewSet para ellos
    # FormSerializer, FormQuestionSerializer
)
# ----------------------------------------------

logger = logging.getLogger(__name__)
User = get_user_model()

# ... (Posibles ViewSets para Form y FormQuestion) ...

class FormResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Respuestas a Formularios (Form Responses).
    """
    # Usa el serializer importado correctamente
    serializer_class = FormResponseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'form': ['exact'], 'form__title': ['icontains'],
        'question': ['exact'], 'question__text': ['icontains'],
        'customer__user__username': ['exact', 'icontains'],
        'customer__company_name': ['icontains'],
        'created_at': ['date', 'date__gte', 'date__lte'],
        'text': ['icontains']
    }

    def get_queryset(self):
        # ... (lógica sin cambios) ...
        user = self.request.user
        base_qs = FormResponse.objects.select_related(
            'customer', 'customer__user', 'form', 'question'
        )

        if hasattr(user, 'customer_profile') and user.customer_profile:
            return base_qs.filter(customer=user.customer_profile)
        elif hasattr(user, 'employee_profile'):
            checker = CanViewFormResponses()
            if checker.has_permission(request=self.request, view=self):
                return base_qs.all()
            else:
                return FormResponse.objects.none()
        else:
            return FormResponse.objects.none()

    def perform_create(self, serializer):
        # ... (lógica sin cambios) ...
        user = self.request.user
        if hasattr(user, 'customer_profile') and user.customer_profile:
            # El serializer ya tiene customer como write_only=True, required=False
            serializer.save(customer=user.customer_profile)
        else:
            raise PermissionDenied(_("Solo los clientes autenticados pueden enviar respuestas de formulario."))

    def perform_update(self, serializer):
        # ... (lógica sin cambios) ...
        raise PermissionDenied(_("Las respuestas de formulario no pueden ser modificadas una vez enviadas."))

    def perform_destroy(self, instance):
        # ... (lógica sin cambios) ...
        user = self.request.user
        checker = IsAdminOrDragon()
        if not checker.has_permission(request=self.request, view=self):
            raise PermissionDenied(_("No tienes permiso para eliminar esta respuesta."))
        instance.delete()


    @action(detail=False, methods=['post'],
            serializer_class=FormResponseBulkCreateSerializer, # Usa el serializer importado
            permission_classes=[IsAuthenticated])
    def bulk_create(self, request):
        # ... (lógica sin cambios, usa el servicio) ...
        user = request.user
        if not hasattr(user, 'customer_profile') or not user.customer_profile:
            return Response(
                {"detail": _("Solo los clientes pueden usar la creación masiva de respuestas.")},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            created_responses = FormResponseService.bulk_create_responses(
                serializer.validated_data,
                user.customer_profile
            )
            return Response(
                {"message": _("Respuestas creadas exitosamente."), "count": len(created_responses)},
                status=status.HTTP_201_CREATED
            )
        except ValueError as ve:
            logger.warning(f"Error de validación en bulk_create FormResponse por {user.username}: {ve}")
            return Response({"detail": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado en bulk_create FormResponse por {user.username}: {e}", exc_info=True)
            return Response(
                {"detail": _("Ocurrió un error interno procesando las respuestas.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# FIN DE views_.txt
```

### 2.3. Serializers Antiguos (`serializers_.txt`)

```python
# <CONTENIDO COMPLETO DE serializers_.txt>
# COMIENZO DE serializers_.txt

# --- START OF FILE authentication.py ---

# api/serializers/authentication.py
"""
Serializers relacionados con la autenticación y obtención de tokens.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# Importar serializers base necesarios
from .base import BasicUserSerializer

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            # Optimización: Cargar datos necesarios para BasicUserSerializer
            user = User.objects.select_related(
                'profile__primary_role',
                'employee_profile__position'
            ).prefetch_related(
                'secondary_role_assignments__role'
            ).get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed(_("El usuario no existe."), code="user_not_found")

        if not user.check_password(password):
            raise AuthenticationFailed(_("Contraseña incorrecta."), code="invalid_credentials")

        if not user.is_active:
            raise AuthenticationFailed(_("Tu cuenta está inactiva."), code="user_inactive")

        data = super().validate(attrs) # Obtiene access y refresh

        # Añadir datos del usuario usando BasicUserSerializer
        user_data = BasicUserSerializer(user).data # 'user' ya tiene datos precargados
        data.update({'user': user_data})
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Añadir claims personalizados al token JWT
        token['roles'] = user.get_all_active_role_names
        token['primary_role'] = user.primary_role_name
        token['username'] = user.username
        token['is_dragon'] = user.is_dragon()
        return token
# --- START OF FILE utilities.py ---

# api/serializers/utilities.py
"""
Serializers para utilidades como Notificaciones y Logs de Auditoría.
"""
from rest_framework import serializers

# Importar modelos necesarios
from ..models import Notification, AuditLog

# Importar serializers base/relacionados
from .base import BasicUserSerializer # Para mostrar info de usuario

class NotificationSerializer(serializers.ModelSerializer):
    """ Serializer para MOSTRAR notificaciones. """
    # Mostrar info básica del usuario receptor
    user = BasicUserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'read', 'created_at', 'link']
        # Este serializer es principalmente para lectura desde la vista
        read_only_fields = fields

class AuditLogSerializer(serializers.ModelSerializer):
    """ Serializer para MOSTRAR logs de auditoría. """
    # Mostrar info básica del usuario que realizó la acción
    user = BasicUserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'timestamp', 'target_model', 'target_id', # Añadido target
            'ip_address', 'details' # Añadido IP
            ]
        read_only_fields = fields # Solo lectura
# --- START OF FILE customers.py ---

# api/serializers/customers.py
"""
Serializers específicos para el modelo Customer.
"""
import logging
from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Importar modelos necesarios
from ..models import Customer, UserRole, UserProfile

# Importar serializers relacionados
from .base import BasicUserSerializer
from .users import UserCreateSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomerSerializer(serializers.ModelSerializer):
    """ Serializer para LEER información de un cliente. """
    user = BasicUserSerializer(read_only=True) # Muestra info completa del usuario asociado
    country_display = serializers.CharField(source='get_country_display', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'phone', 'address', 'date_of_birth', 'country',
            'country_display', 'company_name', 'created_at',
            'preferred_contact_method', 'brand_guidelines'
        ]
        read_only_fields = ['id', 'created_at', 'user', 'country_display']

class CustomerCreateSerializer(serializers.ModelSerializer):
    """ Serializer para CREAR un nuevo cliente y su usuario asociado. """
    user = UserCreateSerializer(write_only=True) # Serializer anidado para datos del usuario
    primary_role = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.filter(is_active=True),
        write_only=True,
        required=True,
        help_text=_("ID del rol principal obligatorio para este cliente.")
    )
    country = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            'user', 'primary_role', 'phone', 'address', 'date_of_birth',
            'country', 'company_name', 'preferred_contact_method', 'brand_guidelines'
        ]

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        primary_role_obj = validated_data.pop('primary_role')
        customer_specific_data = validated_data

        # Re-validar unicidad (doble chequeo)
        if User.objects.filter(email=user_data['email']).exists():
            raise ValidationError({'user': {'email': [_('Ya existe un usuario con este email.')]}})
        if User.objects.filter(username=user_data['username']).exists():
             raise ValidationError({'user': {'username': [_('Ya existe un usuario con este nombre de usuario.')]}})

        # Crear usuario
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Asignar is_staff y rol primario
        user.is_staff = False # Clientes NO son staff
        user.save(update_fields=['is_staff'])

        try:
            # Asumiendo que la señal post_save crea UserProfile
            user_profile, profile_created = UserProfile.objects.get_or_create(user=user)
            user_profile.primary_role = primary_role_obj
            user_profile.save(update_fields=['primary_role'])
            user_profile.full_clean()
        except UserProfile.DoesNotExist:
             # Loggear y fallar si no se creó el perfil (muy raro si la señal funciona)
             logger.error(f"Error crítico: No se encontró/creó UserProfile para el usuario {user.username}")
             raise ValidationError(_("Error interno al inicializar el perfil de usuario."))
        except ValidationError as e:
             logger.error(f"Error de validación al asignar rol primario a {user.username}: {e.message_dict}")
             user.delete() # Rollback manual
             raise ValidationError({'primary_role': e.message_dict.get('primary_role', _('Error asignando rol primario.'))})

        # Crear perfil de Cliente
        customer = Customer.objects.create(user=user, **customer_specific_data)

        # Devolver la instancia de Customer creada
        return customer
# --- START OF FILE base.py ---

# api/serializers/base.py
"""
Contiene serializers base o comunes usados en múltiples módulos.
"""
import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model

# Importar modelos necesarios para estos serializers base
from ..models import Employee, Provider, UserProfile, JobPosition

logger = logging.getLogger(__name__)
User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    """
    Serializer básico para mostrar información del usuario, incluyendo roles
    y el nombre del puesto de trabajo si es un empleado.
    Optimizado para funcionar con datos precargados (select_related/prefetch_related).
    """
    full_name = serializers.SerializerMethodField(read_only=True)
    primary_role = serializers.CharField(source='primary_role_name', read_only=True, allow_null=True)
    primary_role_display_name = serializers.SerializerMethodField(read_only=True, allow_null=True)
    secondary_roles = serializers.ListField(source='get_secondary_active_role_names', read_only=True, child=serializers.CharField())
    all_roles = serializers.ListField(source='get_all_active_role_names', read_only=True, child=serializers.CharField())
    is_dragon_user = serializers.BooleanField(source='is_dragon', read_only=True)
    job_position_name = serializers.SerializerMethodField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff',
            'primary_role', 'primary_role_display_name', 'secondary_roles',
            'all_roles', 'is_dragon_user', 'job_position_name',
        ]
        # No es necesario read_only_fields aquí para SerializerMethodFields o campos con read_only=True

    def get_full_name(self, obj):
        name = obj.get_full_name()
        return name if name else obj.username

    def get_primary_role_display_name(self, obj):
        primary_role_instance = getattr(obj, 'primary_role', None)
        if primary_role_instance and hasattr(primary_role_instance, 'display_name'):
            return primary_role_instance.display_name
        try:
            # Fallback (menos eficiente)
            profile = getattr(obj, 'profile', None)
            if profile and profile.primary_role:
                return profile.primary_role.display_name
        except UserProfile.DoesNotExist:
             logger.warning(f"Perfil no encontrado para usuario {obj.username} en get_primary_role_display_name.")
        except Exception as e:
            logger.error(f"Error obteniendo display_name de ROL para usuario {obj.username}: {e}")
        return None

    def get_job_position_name(self, obj):
        try:
            employee_profile = getattr(obj, 'employee_profile', None)
            position = getattr(employee_profile, 'position', None)
            if position and hasattr(position, 'name'):
                return position.name
        except Employee.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error inesperado obteniendo job_position_name para {obj.username}: {e}", exc_info=True)
        return None

class EmployeeBasicSerializer(serializers.ModelSerializer):
    """ Serializer muy básico para info mínima de empleado, usando BasicUserSerializer. """
    user = BasicUserSerializer(read_only=True)
    class Meta:
        model = Employee
        fields = ['id', 'user']
        read_only_fields = fields

class ProviderBasicSerializer(serializers.ModelSerializer):
     """ Serializer muy básico para info mínima de proveedor. """
     class Meta:
        model = Provider
        fields = ['id', 'name']
        read_only_fields = fields
# --- START OF FILE employees.py ---

# api/serializers/employees.py
"""
Serializers para Empleados y Puestos de Trabajo.
"""
import logging
from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Importar modelos necesarios
from ..models import Employee, JobPosition, UserRole, UserProfile

# Importar serializers relacionados
from .base import BasicUserSerializer
from .users import UserCreateSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

class JobPositionSerializer(serializers.ModelSerializer):
    """ Serializer para el modelo JobPosition. """
    class Meta:
        model = JobPosition
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    """ Serializer para LEER/ACTUALIZAR información de un empleado existente. """
    user = BasicUserSerializer(read_only=True) # Info detallada del usuario (lectura)
    position = JobPositionSerializer(read_only=True) # Info del puesto (lectura)

    # Campo para ACTUALIZAR la posición enviando solo el ID
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosition.objects.all(),
        source='position', # Mapea al campo 'position' del modelo Employee
        write_only=True,   # Solo para escritura
        required=False,    # No obligatorio al actualizar otros campos
        allow_null=True    # Permitir desasignar puesto
    )

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'hire_date', 'address', 'salary',
            'position',     # Para lectura
            'position_id'   # Para escritura (actualización)
        ]
        read_only_fields = ['id', 'hire_date', 'user', 'position']

class EmployeeCreateSerializer(serializers.ModelSerializer):
    """ Serializer para CREAR un nuevo empleado y su usuario asociado. """
    user = UserCreateSerializer(write_only=True) # Datos para crear el usuario
    primary_role = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.filter(is_active=True),
        write_only=True,
        required=True,
        help_text=_("ID del rol principal obligatorio para este empleado.")
    )
    # Campo para ASIGNAR la posición al crear (ID)
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosition.objects.all(),
        source='position', # Mapea al campo 'position' del modelo
        required=False,    # Puesto opcional al crear
        allow_null=True,
        write_only=True    # No se devuelve en la respuesta de creación
    )

    class Meta:
        model = Employee
        fields = [
            'user', 'primary_role', 'position_id',
            'address', 'salary', 'hire_date'
        ]
        extra_kwargs = {
            'hire_date': {'required': False, 'allow_null': True} # Fecha de contratación opcional
        }

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        primary_role_obj = validated_data.pop('primary_role')
        # 'position' ya está manejado por source='position' en position_id
        employee_specific_data = validated_data

        # Validar unicidad
        if User.objects.filter(email=user_data['email']).exists():
            raise ValidationError({'user': {'email': [_('Ya existe un usuario con este email.')]}})
        if User.objects.filter(username=user_data['username']).exists():
             raise ValidationError({'user': {'username': [_('Ya existe un usuario con este nombre de usuario.')]}})

        # Crear usuario
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Asignar is_staff y rol primario
        user.is_staff = True # Empleados SI son staff
        user.save(update_fields=['is_staff'])

        try:
            # Asignar rol primario al perfil (asume señal o crea)
            user_profile, profile_created = UserProfile.objects.get_or_create(user=user)
            user_profile.primary_role = primary_role_obj
            user_profile.save(update_fields=['primary_role'])
            user_profile.full_clean()
        except UserProfile.DoesNotExist:
             logger.error(f"Error crítico: No se encontró/creó UserProfile para empleado {user.username}")
             raise ValidationError(_("Error interno al inicializar el perfil de usuario."))
        except ValidationError as e:
             logger.error(f"Error de validación al asignar rol primario a empleado {user.username}: {e.message_dict}")
             user.delete() # Rollback
             raise ValidationError({'primary_role': e.message_dict.get('primary_role', _('Error asignando rol primario.'))})

        # Crear perfil de Empleado
        # validated_data contiene 'position' gracias a source='position'
        employee = Employee.objects.create(user=user, **employee_specific_data)
        return employee
# --- START OF FILE finances.py ---

# api/serializers/finances.py
"""
Serializers para Facturas, Pagos, Métodos de Pago y Tipos de Transacción.
"""
from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Importar modelos necesarios
from ..models import PaymentMethod, TransactionType, Invoice, Payment, Order

class PaymentMethodSerializer(serializers.ModelSerializer):
    """ Serializer para Métodos de Pago. """
    class Meta:
        model = PaymentMethod
        fields = '__all__' # ['id', 'name', 'is_active']

class TransactionTypeSerializer(serializers.ModelSerializer):
    """ Serializer para Tipos de Transacción. """
    class Meta:
        model = TransactionType
        fields = '__all__' # ['id', 'name', 'requires_approval']

class InvoiceBasicSerializer(serializers.ModelSerializer):
    """ Serializer básico para listas de facturas. """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='order.customer.__str__', read_only=True) # Asume __str__ en Customer

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'customer_name', 'date', 'due_date',
            'status', 'status_display', 'total_amount', 'paid_amount', 'balance_due'
        ]
        read_only_fields = fields # Solo lectura

class PaymentReadSerializer(serializers.ModelSerializer):
    """ Serializer para MOSTRAR detalles de un pago. """
    method_name = serializers.CharField(source='method.name', read_only=True)
    transaction_type_name = serializers.CharField(source='transaction_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number', 'method', 'method_name',
            'transaction_type', 'transaction_type_name', 'date', 'amount',
            'currency', 'status', 'status_display', 'transaction_id', 'notes'
        ]
        read_only_fields = fields

class PaymentCreateSerializer(serializers.ModelSerializer):
    """ Serializer para CREAR un nuevo pago. """
    invoice = serializers.PrimaryKeyRelatedField(
         queryset=Invoice.objects.exclude(status__in=getattr(Invoice, 'FINAL_STATUSES', ['PAID', 'CANCELLED', 'VOID'])) # Excluir facturas finales
    )
    method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.filter(is_active=True))
    transaction_type = serializers.PrimaryKeyRelatedField(queryset=TransactionType.objects.all())

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'method', 'transaction_type', 'date', # Añadir date aquí si el usuario lo puede definir
            'amount', 'currency', 'status', 'transaction_id', 'notes'
        ]
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value <= Decimal('0.00'):
             raise ValidationError(_("El monto del pago debe ser positivo."))
        return value

    def validate(self, data):
        invoice = data['invoice']
        amount = data['amount']
        # Usar la property balance_due si existe y es confiable
        if hasattr(invoice, 'balance_due') and amount > invoice.balance_due:
             raise ValidationError(
                 {'amount': _(f"El monto del pago ({amount}) excede el balance pendiente ({invoice.balance_due}).")}
             )
        # Si no, calcular balance manualmente (menos ideal)
        # balance = invoice.total_amount - invoice.paid_amount
        # if amount > balance:
        #     raise ValidationError(...)
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    """ Serializer detallado para ver/crear/actualizar una Factura. """
    # Campos legibles
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    customer_name = serializers.CharField(source='order.customer.__str__', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payments = PaymentReadSerializer(many=True, read_only=True) # Pagos asociados

    # Campo para escribir (FK a Order)
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), # Podrías filtrar órdenes que aún no tienen factura
        write_only=True,
        required=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_id', 'customer_name', 'invoice_number', 'date',
            'due_date', 'status', 'status_display', 'total_amount', 'paid_amount',
            'balance_due', 'notes', 'payments'
        ]
        read_only_fields = [
            'id', 'order_id', 'customer_name', 'invoice_number', # Autogenerado
            'paid_amount', 'status_display', 'total_amount', 'balance_due', 'payments'
        ]
        # 'order' es write_only por definición aquí
# --- START OF FILE forms.py ---

# api/serializers/forms.py
"""
Serializers relacionados con Formularios, Preguntas y Respuestas.
"""
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# Importar modelos necesarios
from ..models import Form, FormQuestion, FormResponse

class FormQuestionSerializer(serializers.ModelSerializer):
    """ Serializer para Preguntas de Formulario. """
    class Meta:
        model = FormQuestion
        # Excluir 'form' si siempre se anida dentro de FormSerializer
        fields = ['id', 'question_text', 'order', 'required']
        # read_only_fields = ['id'] # ID es read_only por defecto

class FormSerializer(serializers.ModelSerializer):
    """ Serializer para Formularios, incluyendo sus preguntas anidadas. """
    questions = FormQuestionSerializer(many=True, read_only=True) # Anidar preguntas
    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'created_at', 'questions']
        read_only_fields = ['id', 'created_at', 'questions'] # Questions se gestionan por separado o al crear el Form

class FormResponseSerializer(serializers.ModelSerializer):
    """ Serializer para ver/crear respuestas individuales a formularios. """
    # Campos legibles para mostrar información relacionada
    customer_name = serializers.CharField(source='customer.__str__', read_only=True)
    form_name = serializers.CharField(source='form.name', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = FormResponse
        fields = [
            'id', 'customer', 'customer_name', 'form', 'form_name',
            'question', 'question_text', 'text', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'customer_name', 'form_name', 'question_text'
        ]
        # Configuración para escritura (creación)
        extra_kwargs = {
            # Customer se asigna en la vista, no se envía en el payload
            'customer': {'write_only': True, 'required': False, 'allow_null': True},
            'form': {'write_only': True, 'required': True, 'queryset': Form.objects.all()},
            'question': {'write_only': True, 'required': True, 'queryset': FormQuestion.objects.all()}
        }

class FormResponseBulkItemSerializer(serializers.Serializer):
    """ Serializer para un item individual dentro de una creación masiva de respuestas. """
    question = serializers.PrimaryKeyRelatedField(queryset=FormQuestion.objects.all(), required=True)
    text = serializers.CharField(max_length=5000, allow_blank=True)

class FormResponseBulkCreateSerializer(serializers.Serializer):
    """ Serializer para la creación masiva de respuestas a un formulario. """
    form = serializers.PrimaryKeyRelatedField(queryset=Form.objects.all(), required=True)
    responses = FormResponseBulkItemSerializer(many=True, required=True, min_length=1) # Debe haber al menos una respuesta

    def validate(self, data):
        """ Valida que todas las preguntas pertenezcan al formulario especificado. """
        form = data['form']
        responses_data = data['responses']
        form_question_ids = set(form.questions.values_list('id', flat=True))
        submitted_question_ids = set()

        for idx, response_item in enumerate(responses_data):
            question = response_item['question']
            # Verificar pertenencia al formulario
            if question.id not in form_question_ids:
                raise ValidationError({
                    f"responses[{idx}].question": f"La pregunta ID {question.id} no pertenece al formulario '{form.name}'."
                })
            # Verificar preguntas duplicadas en el mismo envío
            if question.id in submitted_question_ids:
                 raise ValidationError({
                    f"responses[{idx}].question": f"La pregunta ID {question.id} se ha enviado más de una vez en esta solicitud."
                 })
            submitted_question_ids.add(question.id)

            # Opcional: Validar requeridos aquí si no se hace en otro lugar
            # if question.required and not response_item.get('text', '').strip():
            #    raise ValidationError({f"responses[{idx}].text": "Esta pregunta es requerida y no puede estar vacía."})

        return data
# --- START OF FILE services_catalog.py ---

# api/serializers/services_catalog.py
"""
Serializers para el catálogo de servicios, campañas, precios y características.
"""
from rest_framework import serializers

# Importar modelos necesarios
from ..models import (
    ServiceCategory, Price, ServiceFeature, Service, Campaign, CampaignService
)

class ServiceCategorySerializer(serializers.ModelSerializer):
    """ Serializer para Categorías de Servicio. """
    class Meta:
        model = ServiceCategory
        fields = '__all__' # ['code', 'name']

class PriceSerializer(serializers.ModelSerializer):
    """ Serializer para mostrar historial de Precios. """
    class Meta:
        model = Price
        fields = ['id', 'amount', 'currency', 'effective_date']
        read_only_fields = fields # Solo lectura

class ServiceFeatureSerializer(serializers.ModelSerializer):
    """ Serializer para mostrar Características de Servicio. """
    feature_type_display = serializers.CharField(source='get_feature_type_display', read_only=True)
    class Meta:
        model = ServiceFeature
        # No incluir 'service' si se anida
        fields = ['id', 'feature_type', 'feature_type_display', 'description']
        read_only_fields = ['id', 'feature_type_display']

class ServiceSerializer(serializers.ModelSerializer):
    """ Serializer para leer/escribir información de Servicios. """
    # Campos legibles
    category_name = serializers.CharField(source='category.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.campaign_name', read_only=True, allow_null=True)
    features = ServiceFeatureSerializer(many=True, read_only=True)
    price_history = PriceSerializer(many=True, read_only=True)
    current_eur_price = serializers.SerializerMethodField()

    # Campos para escribir (FKs)
    category = serializers.PrimaryKeyRelatedField(queryset=ServiceCategory.objects.all(), write_only=True)
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all(), write_only=True, required=False, allow_null=True)

    class Meta:
        model = Service
        fields = [
            'code', 'name', 'category', 'category_name', 'campaign', 'campaign_name',
            'is_active', 'ventulab', 'is_package', 'is_subscription', 'audience',
            'detailed_description', 'problem_solved', 'features', 'price_history',
            'current_eur_price'
        ]
        read_only_fields = [
            'code', 'category_name', 'campaign_name', 'features',
            'price_history', 'current_eur_price'
        ]
        # Hacer los campos FK write_only si no se quieren devolver explícitamente
        # extra_kwargs = {
        #     'category': {'write_only': True},
        #     'campaign': {'write_only': True},
        # }

    def get_current_eur_price(self, obj):
        """ Devuelve el monto del precio actual en EUR. """
        price = obj.get_current_price(currency='EUR')
        return price.amount if price else None

class CampaignServiceSerializer(serializers.ModelSerializer):
    """ Serializer para la relación entre Campaña y Servicio. """
    # Campos legibles
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_code = serializers.CharField(source='service.code', read_only=True)
    # Campos para escribir (asociar servicio)
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True)

    class Meta:
        model = CampaignService
        fields = [
            'id', 'campaign', 'service', 'service_code', 'service_name',
            'discount_percentage', 'additional_details'
        ]
        # 'campaign' es read_only si este serializer se anida dentro de CampaignSerializer
        read_only_fields = ['id', 'campaign', 'service_code', 'service_name']

class CampaignSerializer(serializers.ModelSerializer):
    """ Serializer para Campañas, incluyendo servicios asociados. """
    # Mostrar servicios incluidos (lectura)
    included_services = CampaignServiceSerializer(many=True, read_only=True, source='campaignservice_set') # Ajustar source si related_name es diferente

    class Meta:
        model = Campaign
        fields = [
            'campaign_code', 'campaign_name', 'start_date', 'end_date',
            'description', 'target_audience', 'budget', 'is_active',
            'included_services',
        ]
        read_only_fields = ['campaign_code', 'included_services']
# --- START OF FILE orders.py ---

# api/serializers/orders.py
"""
Serializers para Pedidos, Servicios de Pedido y Entregables.
"""
import logging
from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Importar modelos necesarios
from ..models import Order, OrderService, Deliverable, Service, Employee, Provider, Customer

# Importar serializers relacionados/base
from .base import EmployeeBasicSerializer, ProviderBasicSerializer
from .customers import CustomerSerializer # Para OrderReadSerializer
from .services_catalog import ServiceSerializer # Para OrderServiceReadSerializer

logger = logging.getLogger(__name__)


class OrderServiceCreateSerializer(serializers.ModelSerializer):
    """ Serializer para AÑADIR/ACTUALIZAR servicios en una orden. """
    # Usar PrimaryKeyRelatedField para escribir el ID del servicio
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        required=True
    )
    # Precio opcional, se puede calcular o tomar del servicio
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = OrderService
        # Excluir 'order' ya que se asignará al anidar o en la vista
        fields = ['id', 'service', 'quantity', 'price', 'note']
        read_only_fields = ['id']

    def validate_price(self, value):
        if value is not None and value < Decimal('0.00'):
            raise ValidationError(_("El precio no puede ser negativo."))
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError(_("La cantidad debe ser mayor que cero."))
        return value


class OrderServiceReadSerializer(serializers.ModelSerializer):
    """ Serializer para MOSTRAR servicios dentro de una orden. """
    # Mostrar info completa del servicio usando su serializer
    service = ServiceSerializer(read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderService
        fields = ['id', 'service', 'quantity', 'price', 'note']
        read_only_fields = fields


class DeliverableSerializer(serializers.ModelSerializer):
    """ Serializer para LEER/ESCRIBIR información de Entregables. """
    # Campos legibles
    assigned_employee_info = EmployeeBasicSerializer(source='assigned_employee', read_only=True)
    assigned_provider_info = ProviderBasicSerializer(source='assigned_provider', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True) # URL del archivo

    # Campos para escribir (asignar por ID)
    assigned_employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(user__is_active=True),
        write_only=True, required=False, allow_null=True
    )
    assigned_provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.filter(is_active=True),
        write_only=True, required=False, allow_null=True
    )
    # Permitir carga de archivo (usar multipart/form-data)
    file = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Deliverable
        fields = [
            'id', 'order_id', 'description', 'version',
            'file', # Para escribir (subir)
            'file_url', # Para leer (URL)
            'status', 'status_display', 'due_date',
            'assigned_employee', 'assigned_employee_info', # write / read
            'assigned_provider', 'assigned_provider_info', # write / read
            'feedback_notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'version', 'created_at', 'status_display', 'file_url',
            'assigned_employee_info', 'assigned_provider_info'
        ]
        # 'file' es write_only por definición de FileField aquí

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
            return obj.file.url # Fallback si no hay request
        return None

class OrderReadSerializer(serializers.ModelSerializer):
    """ Serializer para LEER detalles completos de una orden. """
    customer = CustomerSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)
    services = OrderServiceReadSerializer(many=True, read_only=True)
    deliverables = DeliverableSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True) # Calculado en modelo/señal

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'employee', 'status', 'status_display',
            'date_received', 'date_required', 'payment_due_date', 'note',
            'priority', 'completed_at', 'total_amount', 'services', 'deliverables'
        ]
        read_only_fields = fields # Solo lectura


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    """ Serializer para CREAR o ACTUALIZAR una orden. """
    # Campos para escribir (FKs por ID)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=True)
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(user__is_active=True),
        required=False, allow_null=True
    )
    # Anidar el serializer de creación/actualización de servicios
    services = OrderServiceCreateSerializer(many=True, required=False) # Lista de servicios

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'employee', 'status', 'date_required',
            'payment_due_date', 'note', 'priority', 'services'
        ]
        read_only_fields = ['id']

    def _create_or_update_services(self, order, services_data):
        """ Helper para crear/actualizar servicios anidados. """
        # Mapear IDs existentes vs nuevos
        current_service_mapping = {s.id: s for s in order.services.all()}
        incoming_service_mapping = {item.get('id'): item for item in services_data if item.get('id')}
        ids_to_update = set(current_service_mapping.keys()) & set(incoming_service_mapping.keys())
        ids_to_delete = set(current_service_mapping.keys()) - ids_to_update
        data_to_create = [item for item in services_data if not item.get('id')]

        # Eliminar los que ya no están
        if ids_to_delete:
            OrderService.objects.filter(order=order, id__in=ids_to_delete).delete()

        # Actualizar los existentes
        for service_id in ids_to_update:
            instance = current_service_mapping[service_id]
            service_data = incoming_service_mapping[service_id]
            service_obj = service_data.get('service') # PKRelatedField ya validó

            # Obtener precio si no se especificó
            price = service_data.get('price')
            if price is None and service_obj:
                current_price_obj = service_obj.get_current_price(currency='EUR') # Asume EUR o ajusta
                price = current_price_obj.amount if current_price_obj else Decimal('0.00')

            # Actualizar instancia
            instance.service = service_obj
            instance.quantity = service_data.get('quantity', instance.quantity)
            instance.price = price
            instance.note = service_data.get('note', instance.note)
            # No guardar aquí, hacerlo en bulk_update si es posible
            # instance.save() # Alternativa si no hay bulk_update

        # Crear los nuevos
        services_to_create_bulk = []
        for service_data in data_to_create:
            service_obj = service_data.get('service')
            price = service_data.get('price')
            if price is None and service_obj:
                 current_price_obj = service_obj.get_current_price(currency='EUR')
                 price = current_price_obj.amount if current_price_obj else Decimal('0.00')

            services_to_create_bulk.append(OrderService(
                order=order,
                service=service_obj,
                quantity=service_data.get('quantity', 1),
                price=price,
                note=service_data.get('note', '')
            ))

        if services_to_create_bulk:
            OrderService.objects.bulk_create(services_to_create_bulk)

        # Actualizar (si hay cambios y Django >= 4)
        # services_to_update = [current_service_mapping[sid] for sid in ids_to_update]
        # if services_to_update:
        #     OrderService.objects.bulk_update(services_to_update, ['service', 'quantity', 'price', 'note'])


    @transaction.atomic
    def create(self, validated_data):
        services_data = validated_data.pop('services', [])
        order = Order.objects.create(**validated_data)
        self._create_or_update_services(order, services_data)
        # La señal post_save/delete de OrderService debería recalcular total_amount
        order.refresh_from_db()
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        services_data = validated_data.pop('services', None) # None si no se envía el campo
        # Actualizar campos de Order
        instance = super().update(instance, validated_data)

        if services_data is not None: # Si se envió el campo 'services' (incluso vacío)
            self._create_or_update_services(instance, services_data)

        # Señal debería recalcular total_amount
        instance.refresh_from_db()
        return instance
# --- START OF FILE providers.py ---

# api/serializers/providers.py
"""
Serializers para Proveedores.
"""
from rest_framework import serializers

# Importar modelos necesarios
from ..models import Provider, Service

# Importar serializers relacionados
from .services_catalog import ServiceSerializer # Para mostrar detalles de servicios

class ProviderSerializer(serializers.ModelSerializer):
    """ Serializer para leer/escribir información de Proveedores. """
    # Mostrar detalles de servicios (lectura)
    services_provided_details = ServiceSerializer(source='services_provided', many=True, read_only=True)
    # Campo para escribir (asignar servicios por ID)
    services_provided = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Provider
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone', 'rating',
            'is_active', 'notes',
            'services_provided',             # Para escribir
            'services_provided_details'      # Para leer
        ]
        read_only_fields = ['id', 'services_provided_details']
        # 'services_provided' es write_only por definición
# --- START OF FILE users.py ---

# api/serializers/users.py
"""
Serializers para la gestión de usuarios, roles y asignaciones.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Importar modelos necesarios
from ..models import UserRole, UserRoleAssignment

# Importar serializers base/relacionados
from .base import BasicUserSerializer

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer para crear nuevos usuarios. """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmar Contraseña")

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': True} # Email es obligatorio
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise ValidationError({"password": "Las contraseñas no coinciden."})
        # Validar email único
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
             raise ValidationError({'email': _('Ya existe un usuario con este email.')})
        # Validar username único
        username = attrs.get('username')
        if username and User.objects.filter(username=username).exists():
             raise ValidationError({'username': _('Ya existe un usuario con este nombre de usuario.')})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'], # create_user hashea
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        # is_staff se maneja en CustomerCreate/EmployeeCreate
        return user

class UserRoleSerializer(serializers.ModelSerializer):
    """ Serializer para el modelo UserRole. """
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer para gestionar asignaciones de roles secundarios. """
    # Mostrar info del usuario y rol (lectura)
    user_info = BasicUserSerializer(source='user', read_only=True)
    role_info = UserRoleSerializer(source='role', read_only=True)
    # Campos para crear/actualizar (escritura)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=UserRole.objects.filter(is_active=True), write_only=True)

    class Meta:
        model = UserRoleAssignment
        fields = ['id', 'user', 'user_info', 'role', 'role_info', 'is_active', 'assigned_at', 'updated_at']
        read_only_fields = ['id', 'user_info', 'role_info', 'assigned_at', 'updated_at']

# FIN DE serializers_.txt
```

---

## 3. Estructura del Proyecto Nueva (Objetivo Actual)

```text
.
├── .env
├── .gitignore
├── generate_structure.py
├── manage.py
├── project_structure.md
├── pyproject.toml
├── README.md
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py # Este será eliminado o renombrado a __init__.py en settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── settings    # Directorio para base.py, development.py, production.py
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
└── src
    ├── __init__.py
    ├── core
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py # Puede estar vacío si se usan modelos de subdirectorio
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── tests.py  # Puede ser un directorio tests/
    │   ├── urls.py
    │   ├── views.py  # Puede estar vacío si se usan vistas de subdirectorio
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models      # Subdirectorio para modelos específicos
    │   │   ├── __init__.py
    │   │   ├── audit.py
    │   │   ├── notification.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   ├── serializers # Subdirectorio para serializers
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   ├── services    # Subdirectorio para lógica de negocio
    │   │   ├── __init__.py
    │   │   ├── auth_service.py
    │   │   └── tenant_service.py
    │   ├── tests       # Directorio de pruebas
    │   │   └── __init__.py
    │   └── views       # Subdirectorio para vistas (puede estar vacío)
    │       └── __init__.py
    ├── ds_owari        # App para lógica interna de Owari/Doruain
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── urls.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models      # Subdirectorio con modelos: client.py, employee.py, service_offering.py, campaign.py, order.py, internal_finance.py, provider.py
    │   │   └── __init__.py
    │   ├── serializers
    │   │   └── __init__.py
    │   ├── services    # Subdirectorio con servicios: order_fulfillment_service.py
    │   │   └── __init__.py
    │   ├── tests
    │   │   └── __init__.py
    │   └── views
    │       └── __init__.py
    ├── modules         # Contenedor para módulos de producto SaaS
    │   ├── __init__.py
    │   ├── crm
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py # Puede estar vacío
    │   │   ├── permissions.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   ├── views.py  # Puede estar vacío
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   │   ├── models    # Subdirectorio con modelos: customer.py (del tenant), contact.py, form.py, form_response.py
    │   │   │   └── __init__.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── tests
    │   │   │   └── __init__.py
    │   │   └── views
    │   │       └── __init__.py
    │   ├── dashboard_module
    │   │   ├── ... # (estructura similar con subdirectorios models, serializers, views, services)
    │   ├── finances
    │   │   ├── ... # (estructura similar, modelos: invoice.py (del tenant), payment.py)
    │   ├── project_management
    │   │   ├── ... # (estructura similar, modelos: project.py, task.py)
    │   └── service_catalog_management # Opcional si tenants definen sus servicios
    │       ├── ...
    └── shared_utils    # Para utilidades compartidas entre apps
        ├── __init__.py
        ├── apps.py # Opcional, solo si necesita configuración de app
        ├── permissions.py # Clases base de permisos
        ├── utils.py       # Funciones helper
        # No suele tener modelos propios, pero podría tener serializers o vistas base.
        ├── models # Generalmente vacío o con Abstract Models
        │   └── __init__.py
        ├── serializers
        │   └── __init__.py
        ├── services
        │   └── __init__.py
        └── views
            └── __init__.py
```

---

## 4. Plan de Refactorización y Decisiones Clave

### 4.1. Plan de Refactorización Base

```markdown
# Plan de Refactorización

El objetivo principal es refactorizar la aplicación monolítica actual en una arquitectura modular, siguiendo la estructura propuesta. Esto facilitará la escalabilidad, el mantenimiento y la posible migración a microservicios en el futuro.

**Estructura Objetivo**

# Estructura del Proyecto

```
.
├── .env
├── .gitignore
├── generate_structure.py
├── manage.py
├── project_structure.md
├── pyproject.toml
├── README.md
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
└── src
    ├── __init__.py
    ├── core
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models
    │   │   ├── __init__.py
    │   │   ├── audit.py
    │   │   ├── notification.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   ├── serializers
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   ├── services
    │   │   ├── __init__.py
    │   │   ├── auth_service.py
    │   │   └── tenant_service.py
    │   ├── tests
    │   │   └── __init__.py
    │   └── views
    │       └── __init__.py
    ├── ds_owari
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── urls.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models
    │   │   └── __init__.py
    │   ├── serializers
    │   │   └── __init__.py
    │   ├── services
    │   │   └── __init__.py
    │   ├── tests
    │   │   └── __init__.py
    │   └── views
    │       └── __init__.py
    ├── modules
    │   ├── __init__.py
    │   ├── crm
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── tests
    │   │   │   └── __init__.py
    │   │   └── views
    │   │       └── __init__.py
    │   ├── dashboard_module
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── tests
    │   │   │   └── __init__.py
    │   │   └── views
    │   │       └── __init__.py
    │   ├── finances
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── tests
    │   │   │   └── __init__.py
    │   │   └── views
    │   │       └── __init__.py
    │   ├── project_management
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── tests
    │   │   │   └── __init__.py
    │   │   └── views
    │   │       └── __init__.py
    │   └── service_catalog_management
    │       ├── __init__.py
    │       ├── admin.py
    │       ├── apps.py
    │       ├── models.py
    │       ├── permissions.py
    │       ├── signals.py
    │       ├── tests.py
    │       ├── urls.py
    │       └── views.py
    │       ├── migrations
    │       │   └── __init__.py
    │       ├── models
    │       │   └── __init__.py
    │       ├── serializers
    │       │   └── __init__.py
    │       ├── services
    │       │   └── __init__.py
    │       ├── tests
    │       │   └── __init__.py
    │       └── views
    │           └── __init__.py
    └── shared_utils
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models.py
        ├── permissions.py
        ├── signals.py
        ├── tests.py
        ├── urls.py
        └── views.py
        ├── migrations
        │   └── __init__.py
        ├── models
        │   └── __init__.py
        ├── serializers
        │   └── __init__.py
        ├── services
        │   └── __init__.py
        ├── tests
        │   └── __init__.py
        └── views
            └── __init__.py

**Pasos de la Refactorización**

1.  **Creación de las apps:**
    *   Crear el directorio `src/`.
    *   Crear las apps principales (`core`, `ds_owari`) y el directorio `modules/`.
    *   Crear las apps de módulos (`crm`, `project_management`, `finances`, etc.) dentro de `modules/`.
    *   Crear los archivos `__init__.py` y `apps.py` dentro de cada app, y los subdirectorios (`models`, `views`, `serializers`, `services`, `tests`, `migrations`).

2.  **Definición/Movimiento de modelos:**
    *   **`src/core/`**: Definir `Tenant`, `CustomUser` (con FK a `Tenant`), `UserProfile`, `UserRole`, `AuditLog`, `Notification`.
    *   **`src/ds_owari/`**: Mover modelos específicos de Owari/Doruain (sus clientes, empleados, ofertas de servicios, pedidos internos, finanzas internas, proveedores).
    *   **`src/modules/`**: Definir modelos para cada módulo (`Project`, `Task` en `project_management`; `Customer` del tenant, `Form` en `crm`; `Invoice` del tenant en `finances`). **Todos estos deben tener FK a `core.Tenant`**.
    *   Actualizar todas las referencias de FK/M2M a la nueva ruta completa del modelo (ej. `'src.core.Tenant'`).

3.  **Movimiento de vistas, serializers, servicios, signals, permissions:**
    *   Mover el código existente a los archivos y subdirectorios correctos dentro de cada nueva app.
    *   Actualizar todas las importaciones.
    *   **Adaptar vistas en `src/modules/` para filtrar por `request.user.tenant` y asignar `tenant` en la creación.**

4.  **Creación/Actualización de URLs:**
    *   Crear `urls.py` para cada app.
    *   Actualizar `config/urls.py` para incluir las URLs de cada app bajo prefijos lógicos.

5.  **Refactorización de la configuración (`config/settings/`):**
    *   Usar `base.py`, `development.py`, `production.py`.
    *   Actualizar `INSTALLED_APPS` para reflejar la nueva estructura `src.app_name.apps.AppConfigName`.
    *   Configurar `AUTH_USER_MODEL = 'src.core.CustomUser'`.

6.  **Migraciones:**
    *   **Borrar migraciones antiguas.**
    *   Generar nuevas migraciones para cada app: `python manage.py makemigrations app_name`.
    *   Aplicar migraciones: `python manage.py migrate`. (Sobre una BD limpia o con un plan de migración de datos si es necesario).

7.  **Implementación de pruebas:**
    *   Crear directorios `tests/` dentro de cada app.
    *   Implementar pruebas unitarias y de integración, especialmente para la lógica multi-tenant.

8.  **Documentación:**
    *   Actualizar `README.md`.
    *   Documentar APIs (Swagger/OpenAPI).
```

### 4.2. Resumen de Decisiones Clave Adicionales

*   Se adoptó la estructura modular con `src/core/`, `src/modules/`, y `src/ds_owari/`.
*   El modelo `core.Tenant` es central para la visión SaaS y el aislamiento de datos.
*   Los datos en `src/modules/` deben estar aislados por `Tenant` a través de `ForeignKey` y filtrado en vistas/servicios.
*   `ds_owari` gestionará las operaciones internas de Owari/Doruain, interactuando con `core` y potencialmente con `modules` para la prestación de servicios a clientes que también son tenants.
*   La API de Dloub+ (expuesta por `core` y `modules`) servirá tanto para Kukenan (portal cliente) como para posibles interfaces internas.
*   Se aplicarán principios SOLID, con lógica de negocio encapsulada en `services/` dentro de cada app.
*   Se usarán referencias string en modelos para `ForeignKey` y `ManyToManyField` para gestionar dependencias.
*   Las señales se conectarán en el método `ready()` de la `AppConfig` de cada app.

---

## 5. (Opcional) Fragmentos de Código Clave de la Nueva Estructura (A medida que se desarrollen)

*Ejemplos de cómo se verían `INSTALLED_APPS`, `AUTH_USER_MODEL`, el modelo `Tenant`, una vista de módulo con filtrado por tenant, etc.*

```python
# Ejemplo: config/settings/base.py
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     # ...
#     'src.core.apps.CoreConfig',
#     'src.modules.crm.apps.CrmConfig',
#     'src.ds_owari.apps.DsOwariConfig', # Anteriormente OwariInternalConfig
#     # ...
# ]
# AUTH_USER_MODEL = 'src.core.CustomUser' # O como se llame tu User en core.models.user

# Ejemplo: src/core/models/tenant.py
# from django.db import models
# class Tenant(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     # ... otros campos ...
#     def __str__(self):
#         return self.name

# Ejemplo: src/modules/project_management/views.py
# from rest_framework import viewsets
# from .models import Project
# from .serializers import ProjectSerializer
# from src.shared_utils.views import TenantScopedViewSetMixin # Suponiendo que creas este mixin

# class ProjectViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
#     queryset = Project.objects.all() # El mixin se encargará del filtrado por tenant
#     serializer_class = ProjectSerializer
#     # ... permisos ...
```

---
```

