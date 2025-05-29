# src/ds_owari/models/order.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # Asegúrate de importar timezone si lo usas en el save de InternalOrder
from decimal import Decimal
from django.db.models import Sum, F

class InternalOrder(models.Model): # Antes Order
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')), ('CONFIRMED', _('Confirmed')),
        ('PLANNING', _('Planning')), ('IN_PROGRESS', _('In Progress')),
        ('QUALITY_CHECK', _('Quality Check')), ('PENDING_DELIVERY', _('Pending Delivery')),
        ('DELIVERED', _('Delivered')), ('CANCELLED', _('Cancelled')),
        ('ON_HOLD', _('On Hold')), # Añadido para completar el ejemplo de tu archivo original
    ]
    FINAL_STATUSES = ['DELIVERED', 'CANCELLED']

    # Todos los campos deben estar indentados un nivel
    client = models.ForeignKey(
        'app_ds_owari.Client',
        on_delete=models.PROTECT,
        related_name='internal_orders'
    )
    assigned_employee = models.ForeignKey(
        'app_ds_owari.Employee',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='managed_internal_orders'
    )
    date_received = models.DateTimeField(_("Date Received"), auto_now_add=True)
    date_required = models.DateTimeField(_("Date Required"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    payment_due_date = models.DateTimeField(_("Payment Due Date"), null=True, blank=True)
    note = models.TextField(_("Internal Note"), null=True, blank=True)
    priority = models.PositiveIntegerField(_("Priority"), default=3)
    completed_at = models.DateTimeField(_("Completion Date"), null=True, blank=True, editable=False)
    total_amount = models.DecimalField(
        _("Total Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )

    class Meta: # Indentado correctamente
        verbose_name = _("Owari Internal Order")
        verbose_name_plural = _("Owari Internal Orders")
        ordering = ['priority', '-date_received']

    def __str__(self): # Indentado correctamente
        # Acceso seguro a self.client y sus atributos
        client_display = str(self.client) if hasattr(self, 'client') and self.client else "N/A"
        return f"Internal Order #{self.id} for {client_display}"

    def update_total_amount(self): # Indentado correctamente
        # Asegúrate de que el related_name 'service_lines' esté definido en InternalOrderServiceLine.order
        if hasattr(self, 'service_lines'):
            total_agg = self.service_lines.aggregate(
                total=Sum(F('price') * F('quantity'))
            )
            calculated_total = total_agg['total'] if total_agg['total'] is not None else Decimal('0.00')
            if self.pk and self.total_amount != calculated_total:
                InternalOrder.objects.filter(pk=self.pk).update(total_amount=calculated_total)
                self.total_amount = calculated_total
        elif self.pk and self.total_amount != Decimal('0.00'): # Si no hay service_lines, el total debería ser 0
            InternalOrder.objects.filter(pk=self.pk).update(total_amount=Decimal('0.00'))
            self.total_amount = Decimal('0.00')

    # Ejemplo de cómo manejar completed_at en el save, similar al Order original
    def save(self, *args, **kwargs):
        if self.pk: # Solo si ya existe, para comparar con el estado anterior
            try:
                original_instance = InternalOrder.objects.get(pk=self.pk)
                if self.status == 'DELIVERED' and original_instance.status != 'DELIVERED':
                    self.completed_at = timezone.now()
                elif self.status != 'DELIVERED' and original_instance.status == 'DELIVERED':
                    self.completed_at = None
            except InternalOrder.DoesNotExist:
                if self.status == 'DELIVERED' and not self.completed_at: # Nuevo y ya DELIVERED
                     self.completed_at = timezone.now()
        elif self.status == 'DELIVERED' and not self.completed_at: # Nuevo y DELIVERED
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)


class InternalOrderServiceLine(models.Model): # Antes OrderService
    order = models.ForeignKey(
        InternalOrder, # Referencia local
        on_delete=models.CASCADE,
        related_name='service_lines' # Asegúrate que este related_name se usa en update_total_amount
    )
    service_offering = models.ForeignKey( # Indentado correctamente
        'app_ds_owari.ServiceOffering',
        on_delete=models.PROTECT,
        related_name='internal_order_lines'
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    price = models.DecimalField(_("Unit Price"), max_digits=12, decimal_places=2)
    note = models.TextField(_("Note"), blank=True)

    class Meta: # Indentado correctamente
        verbose_name = _("Owari Internal Order Service Line")
        verbose_name_plural = _("Owari Internal Order Service Lines")
        ordering = ['order', 'id'] # Añadido ordering

    def __str__(self): # Indentado correctamente
        service_name = self.service_offering.name if hasattr(self, 'service_offering') and self.service_offering else "N/A"
        order_id_display = self.order_id if hasattr(self, 'order_id') else "N/A"
        return f"{service_name} for Internal Order #{order_id_display}"

    # save() method para auto-precio puede mantenerse similar, usando ServiceOffering
    def save(self, *args, **kwargs):
        if not self.pk and (self.price is None or self.price <= Decimal('0.00')):
            base_price = None
            if hasattr(self, 'service_offering') and self.service_offering:
                try:
                    # Asumiendo que ServiceOffering tiene un método get_current_price
                    # o accedes directamente a un campo de precio.
                    # Esto es un placeholder, ajusta a cómo obtienes el precio de ServiceOffering.
                    price_obj = self.service_offering.price_history.order_by('-effective_date').first()
                    if price_obj:
                        base_price = price_obj.amount

                except Exception as e:
                    # logger.error(f"Error obteniendo precio para ServiceOffering {self.service_offering_id}: {e}")
                    pass # Considera loguear
            self.price = base_price if base_price is not None else Decimal('0.00')
        super().save(*args, **kwargs)


class InternalTask(models.Model): # Antes Deliverable
    STATUS_CHOICES = [
        ('PENDING', _('Pending')), ('ASSIGNED', _('Assigned')),
        ('IN_PROGRESS', _('In Progress')), # Añadido para completar
        ('PENDING_APPROVAL', _('Pending Approval Client')),
        ('PENDING_INTERNAL_APPROVAL', _('Pending Internal Approval')),
        ('REQUIRES_INFO', _('Requires Info Additional')),
        ('REVISION_REQUESTED', _('Revision Requested')),
        ('APPROVED', _('Approved')),
        ('COMPLETED', _('Completed')), ('REJECTED', _('Rejected')),
    ]
    FINAL_STATUSES = ['COMPLETED', 'REJECTED']

    order = models.ForeignKey(
        InternalOrder, # Referencia local
        on_delete=models.CASCADE,
        related_name='internal_tasks'
    )
    file = models.FileField(
        _("File"),
        upload_to='ds_owari/tasks/%Y/%m/', # Ruta específica
        null=True,
        blank=True
    )
    description = models.TextField(_("Description"))
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)
    version = models.PositiveIntegerField(_("Version"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    assigned_employee = models.ForeignKey( # Indentado correctamente
        'app_ds_owari.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_internal_tasks'
    )
    assigned_provider = models.ForeignKey( # Indentado correctamente
        'app_ds_owari.Provider',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_internal_tasks_provider'
    )
    feedback_notes = models.TextField(_("Feedback Notes"), blank=True)

    class Meta: # Indentado correctamente
        verbose_name = _("Owari Internal Task")
        verbose_name_plural = _("Owari Internal Tasks")
        ordering = ['order', 'due_date', 'created_at']

    def __str__(self): # Indentado correctamente
        order_id_display = self.order_id if hasattr(self, 'order_id') else "N/A"
        return f"Internal Task: {self.description[:30]}... for Order #{order_id_display}"