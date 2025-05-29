# src/modules/finances/models/invoice.py
from django.db import models
from django.utils.translation import gettext_lazy as _
# from django.utils import timezone # No se usa directamente aquí, pero es bueno tenerlo
from decimal import Decimal
import datetime # Asegúrate de que este import esté presente

class Invoice(models.Model): # Factura DEL TENANT
    tenant = models.ForeignKey(
        'core.Tenant', # Asume que CoreConfig tiene label = 'core'
        on_delete=models.CASCADE,
        related_name='tenant_invoices'
    )
    project = models.ForeignKey(
        'app_project_management.Project', # CORREGIDO: Usa la label de ProjectManagementConfig
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoices'
    )
    customer = models.ForeignKey(
      'app_crm.Customer', # Asume que CrmConfig tiene label = 'app_crm'
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True, blank=True
    )
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, blank=True)
    date = models.DateField(_("Issue Date"), default=datetime.date.today)
    due_date = models.DateField(_("Due Date"))
    total_amount_manual = models.DecimalField(
        _("Total Amount (Manual)"), max_digits=12, decimal_places=2,
        null=True, blank=True
    )
    paid_amount = models.DecimalField(_("Amount Paid"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    status = models.CharField(
        _("Status"), max_length=20,
        choices=[('DRAFT', _('Draft')), ('SENT', _('Sent')), ('PAID', _('Paid')),
                ('CANCELLED', _('Cancelled')), ('VOID', _('Void'))], # Simplificado, añade más si los necesitas
        default='DRAFT', db_index=True
    )
    notes = models.TextField(_("Notes/Terms"), blank=True)

    class Meta:
        verbose_name = _("Tenant Invoice")
        verbose_name_plural = _("Tenant Invoices")
        unique_together = (('tenant', 'invoice_number'),)
        ordering = ['tenant', '-date', '-id']

    def __str__(self):
        return f"Invoice {self.invoice_number} (Tenant: {self.tenant.name if self.tenant else 'N/A'})"