# src/modules/finances/models/payment.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal

class Payment(models.Model): # Pago recibido POR EL TENANT
    invoice = models.ForeignKey(
        'app_finances.Invoice', # CORREGIDO: Usa la label de FinancesConfig
        on_delete=models.CASCADE, related_name='payments'
    )
    method = models.ForeignKey(
        'app_finances.PaymentMethod', # CORREGIDO: Usa la label de FinancesConfig
        on_delete=models.PROTECT, verbose_name=_("Payment Method")
    )
    transaction_type = models.ForeignKey(
        'app_finances.TransactionType', # CORREGIDO: Usa la label de FinancesConfig
        on_delete=models.PROTECT, verbose_name=_("Transaction Type")
    )
    date = models.DateTimeField(_("Payment Date"), default=timezone.now)
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='EUR')
    status = models.CharField(
        _("Status"), max_length=20,
        choices=[('PENDING', _('Pending')), ('COMPLETED', _('Completed')),
                ('REFUNDED', _('Refunded'))], # Simplificado
        default='COMPLETED', db_index=True
    )
    transaction_id = models.CharField(_("External Transaction ID"), max_length=100, blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Tenant Payment")
        verbose_name_plural = _("Tenant Payments")
        ordering = ['-date']

    def __str__(self):
        invoice_display = self.invoice.invoice_number if self.invoice else "N/A"
        return f"Payment {self.amount} {self.currency} for Invoice {invoice_display}"